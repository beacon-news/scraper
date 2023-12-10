import pytest
from bs4 import BeautifulSoup, Tag
from src.scraper.config import ComponentSelector
from src.scraper.process_selectors import process_selectors

class TestProcessSelector:

  _elem: Tag = None

  @pytest.fixture(scope="class")
  def test_html_tree(self) -> Tag:
    html_str = """
    <html>

      <div>
        <p>foo</p>
        <p>bar</p>
        <main>
          <span>span_foo</span>
          <span>span_bar</span>
        </main>
      </div>
      <div>
        <p>baz</p>
        <main>
          <span>span_baz</span>
        </main>
      </div>

    </html>
    """
    soup = BeautifulSoup(html_str, "html.parser")
    html = soup.select_one("html")
    if html is None:
      raise Exception("no root 'html' element found")
    return html
  
  @pytest.mark.parametrize("selector_config, expected", [
    (
      # select first element
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
      # select all elements
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
      # nested (single child) select first
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
      # nested (single child) select all
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
      # nested (multi child) select first
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
            "first_p": "baz"
          }
        ]
      }
    ),
    (
      # nested (multi child) select all
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
            "all_ps": ["baz"]
          }
        ]
      }
    ),
    (
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
                "spans": ["span_baz"]
              }
            ]
          }
        ],
      }
    )
  ])
  def test_selector_result(self, selector_config: dict, expected: dict, test_html_tree):
    s = ComponentSelector(selector_config)
    result = process_selectors(s, test_html_tree)
    assert result == expected
