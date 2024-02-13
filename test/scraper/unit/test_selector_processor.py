import pytest
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
    ),
    (
      # test regex prop extractor for matching
      """
      <html>
        <p>blah foo blah</p>
        <p>This string doesn't contain only bar</p>
      </html>
      """,
      {
        "key": "original_match",
        "select": "all",
        "extract": {
          "type": "text",
          "regex_extractor": {
            "regex": [
              ".*foo.*"
            ]
          }
        },
      },
      {
        "original_match": [
          "blah foo blah"
        ]
      }
    ),
    (
      # test regex prop extractor for returning only the first matching span
      """
      <html>
        <p>blah1 foo blah2</p>
        <p>This string doesn't contain only bar</p>
      </html>
      """,
      {
        "key": "first_match",
        "select": "all",
        "extract": {
          "type": "text",
          "regex_extractor": {
            "return": "first",
            "regex": [
              "blah."
            ]
          }
        },
      },
      {
        "first_match": [
          "blah1", 
        ]
      }
    ),
    (
      # test date extraction (regex + date modifier)
      """
      <html>
        <p id="1">February 13, 2024, 9:03 AM</p>                              <!-- abc news -->
        <p id="2">2024-02-13T16:17:10.000Z</p>                                <!-- bbc news -->
        <p id="3">2024-02-13T12:47:48+00:00</p>                               <!-- bbc news (sports) --> 
        <p id="4">Updated\n        11:22 AM EST, Tue February 13, 2024</p>    <!-- cnn -->
        <p id="5">Published\n        10:39 AM EST, Tue February 13, 2024</p>  <!-- cnn -->
        <p id="6">Updated 4:04 PM GMT+2, February 13, 2024</p>                <!-- ap news -->
      </html>
      """,
      {
        "key": "dates",
        "children": [
          {
            "key": "1",
            "selector": "p[id='1']",
            "extract": {
              "type": "text",
              "modifiers": [
                {
                  "type": "iso_date_modifier",
                }
              ]
            }
          },
          {
            "key": "2",
            "selector": "[id='2']",
            "extract": {
              "type": "text",
              "modifiers": [
                {
                  "type": "iso_date_modifier",
                }
              ]
            }
          },
          {
            "key": "3",
            "selector": "[id='3']",
            "extract": {
              "type": "text",
              "modifiers": [
                {
                  "type": "iso_date_modifier",
                }
              ]
            }
          },
          {
            "key": "4",
            "selector": "[id='4']",
            "extract": {
              "type": "text",
              "regex_extractor": {
                "return": "first",
                "regex": [
                  "[0-9]{2}:[0-9]{2}.*"
                ]
              },
              "modifiers": [
                {
                  "type": "iso_date_modifier",
                }
              ]
            }
          },
          {
            "key": "5",
            "selector": "[id='5']",
            "extract": {
              "type": "text",
              "regex_extractor": {
                "return": "first",
                "regex": [
                  "[0-9]{2}:[0-9]{2}.*"
                ]
              },
              "modifiers": [
                {
                  "type": "iso_date_modifier",
                }
              ]
            }
          },
          {
            "key": "6",
            "selector": "[id='6']",
            "extract": {
              "type": "text",
              "regex_extractor": {
                "return": "first",
                "regex": [
                  "[0-9]{2}:[0-9]{2}.*"
                ]
              },
              "modifiers": [
                {
                  "type": "iso_date_modifier",
                }
              ]
            }
          },
        ]
      },
      {
        "dates": {
          "1": "2024-02-13T09:03:00",
          "2": "2024-02-13T16:17:10+00:00",
          "3": "2024-02-13T12:47:48+00:00",
          "4": "2024-02-13T11:22:00-05:00",
          "5": "2024-02-13T10:39:00-05:00",
          "6": "2024-02-13T16:04:00-02:00",
        }
      }
    ),
  ])
  def test_selector_result(self, html: str, selector_config: dict, expected: dict):
    s = ComponentSelector(selector_config)
    result = SelectorProcessor().process(s, html)
    assert result == expected

