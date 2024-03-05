
# config parsing test
from scraper.src.scraper.config import ComponentSelector, ConfigFactory


if __name__ == "__main__":
  c1 = """
    {
      "pages": [
        {
          "url": "https://www.bbc.com/news/world",
          "url_patterns": [
            "^/news/world-.*-.*"
          ],
          "selectors": {
            "key": "some_key",
            "selector": "div",
            "extract": {
              "type": "text"
            }
          }
        }
      ]
    }
  """
  c2 = """
    {
      "pages": [
        {
          "url": "https://www.bbc.com/news/world",
          "url_patterns": [
            "^/news/world-.*-.*"
          ],
          "selectors": {
            "key": "some_key",
            "selector": "div",
            "child": {
              "key": "child_key",
              "selector": "p",
              "child": {
                "key": "child_child_key",
                "selector": "b"
              }
            },
            "extract": {
              "type": "text"
            }
          }
        }
      ]
    }
  """
  c3 = """
    {
      "pages": [
        {
          "url": "https://www.bbc.com/news/world",
          "url_patterns": [
            "^/news/world-.*-.*"
          ],
          "selectors": {
            "key": "some_key",
            "selector": "div",
            "children": [
              {
                "key": "child_key",
                "selector": "p",
                "child": {
                  "key": "child_child_key",
                  "selector": "span"
                }
              },
              {
                "key": "other_child_key",
                "selector": ".class",
                "children": [
                  {
                    "key": "other_child_child_key",
                    "selector": "img",
                    "select": "all",
                    "child": {
                      "key": "other_child_child_child_key",
                      "selector": "all",
                      "extract": {
                        "type": "attribute",
                        "key": "src"
                      }
                    }
                  },
                  {
                    "key": "another_child_child_key",
                    "selector": "figure",
                    "children": [
                      {
                        "key": "another_child_child_child_key",
                        "selector": "#pic-id",
                        "select": "all"
                      }
                    ] 
                  }
                ]
              }
            ]
          }
        }
      ]
    }
  """

  c = ConfigFactory.from_json_str(c3)

  def walk_selectors_rec(selector: ComponentSelector, indent: int):

    if selector.type == "leaf":
      msg = " ".join([" " * indent, selector.select, selector.type, selector.css_selector])
      print(msg)
      return
    
    if selector.type == "single":
      msg = " ".join([" " * indent, selector.select, selector.type, selector.css_selector])
      print(msg)
      walk_selectors_rec(selector.child, indent + 1)
      return

    if selector.type == "multi":
      msg = " ".join([" " * indent, selector.select, selector.type, selector.css_selector])
      print(msg)
      for s in selector.children:
        walk_selectors_rec(s, indent + 1)
      return

  walk_selectors_rec(selector=c.scrape_configs[0].selectors, indent=0)