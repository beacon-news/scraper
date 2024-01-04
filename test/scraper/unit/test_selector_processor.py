import pytest
from bs4 import BeautifulSoup
from src.scraper.config import ComponentSelector
from src.scraper.selector_processor import SelectorProcessor

class TestProcessSelector:

  @pytest.mark.parametrize("html, selector_config, expected", [
    (
      # select first element
      """
      <html>
        <p>foo</p>
        <p>bar</p>
        <p>baz</p>
      </html>
      """,
      {
        "key": "first_p",
        "selector": "p",
        "select": "first",
        "extract": {
          "type": "text"
        }
      },
      {
        "first_p": "foo"
      }
    ),
    (
      # select first element by default (no 'select' provided)
      """
      <html>
        <p>foo</p>
        <p>bar</p>
        <p>baz</p>
      </html>
      """,
      {
        "key": "first_p",
        "selector": "p",
        "extract": {
          "type": "text"
        }
      },
      {
        "first_p": "foo"
      }
    ),
    (
      # use '*' css selector if no 'selector' is provided
      """
      <html>
        <p>foo</p>
        <p>bar</p>
        <p>baz</p>
      </html>
      """,
      {
        "key": "default_selector",
        "select": "all",
        "extract": {
          "type": "text"
        }
      },
      {
        "default_selector": ["foo", "bar", "baz"]
      }
    ),
    (
      # select all elements
      """
      <html>
        <p>foo</p>
        <p>bar</p>
        <p>baz</p>
      </html>
      """,
      {
        "key": "all_ps",
        "selector": "p",
        "select": "all",
        "extract": {
          "type": "text"
        }
      },
      {
        "all_ps": ["foo", "bar", "baz"]
      }
    ),
    (
      # single child select first
      """
      <html>
        <div>
          <p>foo</p>
          <p>bar</p>
        </div>
        <div>
          <p>foo</p>
          <p>bar</p>
          <p>baz</p>
        </div>
      </html>
      """,
      {
        "key": "first_div",
        "selector": "div",
        "select": "first",
        "child": {
          "key": "first_p",
          "selector": "p",
          "select": "first",
          "extract": {
            "type": "text"
          }
        }
      },
      {
        "first_div": {
          "first_p": "foo"
        }
      }
    ),
    (
      # single child select all
      """
      <html>
        <div>
          <p>foo</p>
          <p>bar</p>
        </div>
        <div>
          <p>foo</p>
          <p>bar</p>
          <p>baz</p>
        </div>
      </html>
      """,
      {
        "key": "first_div",
        "selector": "div",
        "select": "first",
        "child": {
          "key": "all_ps",
          "selector": "p",
          "select": "all",
          "extract": {
            "type": "text"
          }
        }
      },
      {
        "first_div": {
          "all_ps": ["foo", "bar"]
        }
      }
    ),
    (
      # multi child select first
      """
      <html>
        <div>
          <p>foo</p>
          <p>bar</p>
        </div>
        <div>
          <p>foo</p>
          <p>bar</p>
          <p>baz</p>
        </div>
      </html>
      """,
      {
        "key": "all_divs",
        "selector": "div",
        "select": "all",
        "child": {
          "key": "first_p",
          "selector": "p",
          "select": "first",
          "extract": {
            "type": "text"
          }
        }
      },
      {
        "all_divs": [
          {
            "first_p": "foo"
          },
          {
            "first_p": "foo"
          }
        ]
      }
    ),
    (
      # multi child select all
      """
      <html>
        <div>
          <p>foo</p>
          <p>bar</p>
        </div>
        <div>
          <p>foo</p>
          <p>bar</p>
          <p>baz</p>
        </div>
      </html>
      """,
      {
        "key": "all_divs",
        "selector": "div",
        "select": "all",
        "child": {
          "key": "all_ps",
          "selector": "p",
          "select": "all",
          "extract": {
            "type": "text"
          }
        }
      },
      {
        "all_divs": [
          {
            "all_ps": ["foo", "bar"]
          },
          {
            "all_ps": ["foo", "bar", "baz"]
          }
        ]
      }
    ),
    (
      # select in order 
      """
      <html>
        <div>
          <p>foo</p>
          <p>bar</p>
        </div>
        <main>
          <span>span_foo</span>
          <span>span_bar</span>
        </main>
        <div>
          <p>baz</p>
        </div>
      </html>
      """,
      {
        "key": "ordered_test",
        "selector": "div, main",
        "select": "all",
        "children": [
          {
            "key": "ps",
            "selector": "p",
            "select": "all",
            "extract": {
              "type": "text"
            }
          },
          {
            "key": "spans",
            "selector": "span",
            "select": "all",
            "extract": {
              "type": "text"
            }
          }
        ]
      },
      {
        "ordered_test": [
          {
            "ps": ["foo", "bar"]
          },
          {
            "spans": ["span_foo", "span_bar"]
          },
          {
            "ps": ["baz"]
          },
        ]
      }
    ),
    (
      # include_self test
      """
      <html>
        <div> 
          <p>foo</p>
        </div>
      </html>
      """,
      {
        "key": "include_self_test",
        "selector": "div p",
        "child": {
          "key": "p",
          "selector": "p", # also works with 'div p', but 'div' doesn't return anything for some reason...
          "include_self": "true",
        }
      },
      {
        "include_self_test": {
          "p": "foo"
        }
      }
    ),
    (
      # select elements in order (filter) with include_self
      """
      <html>
        <div> 
          <p>foo</p>
          <span>span_foo</span>
          <p>bar</p>
          <span>span_bar</span>
        </div>
      </html>
      """,
      {
        "key": "order_include_self",
        "selector": "div p, div span", # selects p, span in order
        "select": "all",
        "children": [ 
          {
            "key": "p",
            "selector": "p",
            "include_self": "true", # filter them by applying redundant selectors with the parent
          },
          {
            "key": "span",
            "selector": "span",
            "include_self": "true",
          }
        ]
      },
      {
        "order_include_self": [
          {
            "p": "foo"
          },
          {
            "span": "span_foo"
          },
          {
            "p": "bar"
          },
          {
            "span": "span_bar"
          },
        ]
      }
    ),
    (
      # a more complex selector with nested multi child select alls
      """
      <html>
        <div>
          <main>
            <span>span_foo</span>
            <span>span_bar</span>
          </main>
          <p>foo</p>
          <p>bar</p>
        </div>
        <div>
          <main>
            <span>span_foo</span>
            <p>baz</p>
          </main>
          <main>
            <span>span_bar</span>
          </main>
        </div>
      </html>
      """,
      {
        "key": "divs",
        "selector": "div",
        "select": "all",
        "children": [
          {
            "key": "ps",
            "selector": "p",
            "select": "all",
            "extract": {
              "type": "text"
            }
          },
          {
            "key": "mains",
            "selector": "main",
            "select": "all",
            "children": [
              {
                "key": "spans",
                "selector": "span",
                "select": "all",
                "extract": {
                  "type": "text"
                }
              }
            ]
          }
        ]
      },
      {
        "divs": [
          {
            "ps": ["foo", "bar"]
          },
          {
            "mains": [
              {
                "spans": ["span_foo", "span_bar"]
              },
            ]
          },
          {
            "ps": ["baz"]
          },
          {
            "mains": [
              {
                "spans": ["span_foo"]
              },
              {
                "spans": ["span_bar"]
              }
            ]
          }
        ],
      }
    )
  ])
  def test_selector_result(self, html: str, selector_config: dict, expected: dict):
    s = ComponentSelector(selector_config)
    result = SelectorProcessor().process(s, html)
    assert result == expected
