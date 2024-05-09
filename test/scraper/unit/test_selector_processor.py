import pytest
from src.scraper import *

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
        "modifiers": [
          {
            "type": "regex",
            "regex": [
              ".*foo.*"
            ]
          }
        ]
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
        <p>blah4 string</p>
      </html>
      """,
      {
        "key": "first_match_in_every_text",
        "select": "all",
        "modifiers": [
          {
            "type": "regex",
            "return": "first",
            "regex": [
              "blah."
            ]
          }
        ]
      },
      {
        "first_match_in_every_text": [
          "blah1", "blah4" 
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
        <p id="5">Updated 4:04 PM GMT+2, February 13, 2024</p>                <!-- ap news - JavaScript generated... -->
        <p id="6">1709742104000</p>                                           <!-- ap news, UNIX timestamp with millis-->
        <p id="7">1709742104</p>                                              <!-- ap news, UNIX timestamp -->
      </html>
      """,
      {
        "key": "dates",
        "children": [
          {
            "key": "1",
            "selector": "[id='1']",
            "modifiers": [
              {
                "type": "iso_date_parser",
              }
            ]
          },
          {
            "key": "2",
            "selector": "[id='2']",
            "modifiers": [
              {
                "type": "iso_date_parser",
              }
            ]
          },
          {
            "key": "3",
            "selector": "[id='3']",
            "modifiers": [
              {
                "type": "iso_date_parser",
              }
            ]
          },
          {
            "key": "4",
            "selector": "[id='4']",
            "modifiers": [
              {
                "type": "regex",
                "return": "first",
                "regex": [
                  "[0-9]+:[0-9]{2}.*"
                ]
              },
              {
                "type": "iso_date_parser",
              }
            ]
          },
          {
            "key": "5",
            "selector": "[id='5']",
            "modifiers": [
              {
                "type": "regex",
                "return": "first",
                "regex": [
                  "[0-9]+:[0-9]{2}.*"
                ]
              },
              {
                "type": "iso_date_parser",
              }
            ]
          },
          {
            "key": "6",
            "selector": "[id='6']",
            "modifiers": [
              {
                "type": "iso_date_parser",
              }
            ]
          },
          {
            "key": "7",
            "selector": "[id='7']",
            "modifiers": [
              {
                "type": "iso_date_parser",
              }
            ]
          },
        ]
      },
      {
        "dates": [
          {"1": "2024-02-13T09:03:00"},
          {"2": "2024-02-13T16:17:10+00:00"},
          {"3": "2024-02-13T12:47:48+00:00"},
          {"4": "2024-02-13T11:22:00-05:00"},
          {"5": "2024-02-13T16:04:00-02:00"},
          {"6": "2024-03-06T18:21:44"},
          {"7": "2024-03-06T18:21:44"},
        ]
      }
    ),
    (
      # test jsonpath extractor for single and multi-valued return values
      """
      <html>
        <script type="application/json">
          {
            "foo": {
              "bar": [
                {
                  "baz": "blah1"
                },
                {
                  "baz": "blah2"
                }  
              ],
              "other_key": 4242
            },
            "another_key": 42
          }
        </script>
      </html>
      """,
      {
        "key": "json",
        "children": [
          {
            "key": "single",
            "selector": "script",
            "extract": {
              "type": "jsonpath",
              "path": "$.foo.other_key"
            }
          },
          {
            "key": "multiple",
            "selector": "script",
            "extract": {
              "type": "jsonpath",
              "path": "$.foo..baz"
            }
          },
        ]
      },
      {
        "json": [
          {
            "single": "4242",
          },
          {
            "multiple": ["blah1", "blah2"],
          }
        ],
      }
    ),
  ])
  def test_selector_result_no_common_selectors(
    self, 
    html: str, 
    selector_config: dict, 
    expected: dict,
  ):
    s = ComponentSelectorConfig(selector_config)
    result = SelectorProcessor.process_html(s, [], html)
    assert result == expected


  @pytest.mark.parametrize("html, common_selectors, selector_config, expected", [
    (
      # test common selector reference
      """
      <html>
        <p id=1>blah1 foo blah2</p>
        <p>This string doesn't contain only bar</p>
        <p>blah4 string</p>
      </html>
      """,
      [
        {
          "name": "first-p",
          "selector": {
            "key": "first-p-key",
            "selector": "[id='1']",
          } 
        },
      ],
      {
        "common_selector": "first-p"
      },
      {
        "first-p-key": "blah1 foo blah2"
      }
    )
  ])
  def test_selector_result_with_common_selectors(
    self, 
    html: str, 
    common_selectors: list[dict], 
    selector_config: dict, 
    expected: dict,
  ):
    cs = CommonComponentSelectorsConfig(common_selectors)
    s = ComponentSelectorConfig(selector_config)
    
    result = SelectorProcessor.process_html(s, cs, html)
    assert result == expected

  @pytest.mark.parametrize("common_selectors, selector_config, expectation", [
    (
      # test infinite common selector reference
      [
        {
          "name": "first-p",
          "selector": {
            "common_selector": "first-p"
          } 
        },
      ],
      {
        "common_selector": "first-p"
      },
      pytest.raises(ConfigValidationException),
    ),
  ])
  def test_infinite_common_selector_ref_raises(
    self, 
    common_selectors: list[dict], 
    selector_config: dict, 
    expectation,
  ):
    # tests for selector loops
    with expectation:
      print(common_selectors)
      Config({
        "version": "1.0.0",
        "pages": [
          {
            "urls": ["test"],
            "url_selectors": {
              "key": "test",
            },
            "selectors": selector_config,
          }
        ],
        "common_selectors": common_selectors,
      })
    