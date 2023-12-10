import logging
import json

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# TODO: logging
# TODO: encourage duck typing (don't check necessarily the types of stuff, check if we're able to use them)
class ScrapeConfigValidator:

  def must_not_be_none(property: str, value):
    if value is None:
      raise ScrapeConfigValidationException(f"'{property}' field must not be None")
  
  def must_have_type(property: str, value, prop_type: type):
    if not isinstance(value, prop_type):
      raise ScrapeConfigValidationException(f"'{property}' field must be of type {prop_type}")

  def must_have_types(property: str, value, prop_types: list[type]):
    for t in prop_types:
      if isinstance(value, t):
        return
    raise ScrapeConfigValidationException(f"'{property}' field must be one of types {prop_types}")

  def must_have_value(property: str, value, values: list):
    for v in values:
      if value == v:
        return
    
    raise ScrapeConfigValidationException(f"'{property}' field must be one of {values}")
  
  def must_not_be_empty(property: str, value: list):
    if len(value) == 0:
      raise ScrapeConfigValidationException(f"'{property}' field must not be empty")


class ScrapeConfigValidationException(Exception):
  pass

# TODO: every class should check its own type? (check if dict or list, don't let the parent class to do this?)
class Config:
  """
  top-level config
  {
    "pages": ScrapeConfig[]
  }
  """

  prop_pages = "pages"

  def __init__(self, config: dict):
    scrape_config = config.get(Config.prop_pages)
    ScrapeConfigValidator.must_not_be_none(Config.prop_pages, scrape_config)
    ScrapeConfigValidator.must_have_type(Config.prop_pages, scrape_config, list)
    ScrapeConfigValidator.must_not_be_empty(Config.prop_pages, scrape_config)
    self.scrape_configs: list[ScrapeConfig] = []
    for config in scrape_config:
      self.scrape_configs.append(ScrapeConfig(config))

class ConfigFactory:
  def fromJsonString(config_json_string: str) -> Config:
    return Config(json.loads(config_json_string))
  
  def fromJsonFile(self, path: str) -> Config:
    with open(path) as f:
      config = f.read()
    return Config(json.loads(config))



class ScrapeConfig:
  """
  scrape_config_dict format:

  {
    "url": "https://www.bbc.com/news/world",
    "patterns_path": [
      "^/news/world-.*-.*"
    ],
    "selectors": ComponentSelector
  }
  """

  prop_url = "url"
  prop_path_patterns = "path_patterns"
  prop_selectors = "selectors"

  def __init__(self, scrape_config_dict: dict):
    self.url: str = scrape_config_dict.get(ScrapeConfig.prop_url)
    ScrapeConfigValidator.must_not_be_none(ScrapeConfig.prop_url, self.url)
    ScrapeConfigValidator.must_have_type(ScrapeConfig.prop_url, self.url, str)

    self.path_patterns: list[str] = scrape_config_dict.get(ScrapeConfig.prop_path_patterns)
    ScrapeConfigValidator.must_not_be_none(ScrapeConfig.prop_path_patterns, self.path_patterns)
    ScrapeConfigValidator.must_have_type(ScrapeConfig.prop_path_patterns, self.path_patterns, list) # TODO: list of string, actually
    ScrapeConfigValidator.must_not_be_empty(ScrapeConfig.prop_path_patterns, self.path_patterns)

    selectors = scrape_config_dict.get(ScrapeConfig.prop_selectors)
    ScrapeConfigValidator.must_not_be_none(ScrapeConfig.prop_selectors, selectors)
    ScrapeConfigValidator.must_have_types(ScrapeConfig.prop_selectors, selectors, [dict, list])
    self.selectors = ComponentSelector(selectors)

class ComponentSelector:
  """
  'single'
  {
    "key": str,
    "selector": str,
    "select": "first" | "all",
    "child": ComponentSelector
  }
  'multi'
  {
    "key": str,
    "selector": str,
    "children": ComponentSelector[] 
  }
  'leaf'
  {
    "key": str,
    "selector": str,
    "extract": PropExtract
  }
  """

  prop_key = "key"
  prop_css_selector = "selector"
  
  prop_select = "select"
  prop_select_value_first = "first"
  prop_select_value_all = "all"
  prop_select_values = [prop_select_value_first, prop_select_value_all]

  prop_extract = "extract"

  prop_single_child = "child"
  prop_multi_children = "children"

  selector_type_single = "single"
  selector_type_multi = "multi"
  selector_type_leaf = "leaf"

  def __init__(self, config: dict):
    # key is mandatory
    self.key = config.get(ComponentSelector.prop_key)
    ScrapeConfigValidator.must_not_be_none(ComponentSelector.prop_key, self.key)
    ScrapeConfigValidator.must_have_type(ComponentSelector.prop_key, self.key, str)

    # selector can be empty, select everything by default then
    css_selector = config.get(ComponentSelector.prop_css_selector)
    if css_selector is not None:
      ScrapeConfigValidator.must_have_type(ComponentSelector.prop_css_selector, css_selector, str) 
    else:
      css_selector = "*"
    self.css_selector = css_selector 

    # select mode can be empty
    select = config.get(ComponentSelector.prop_select)
    if select is not None:
      ScrapeConfigValidator.must_have_type(ComponentSelector.prop_select, select, str)
      ScrapeConfigValidator.must_have_value(ComponentSelector.prop_select, select, ComponentSelector.prop_select_values)
    else:
      select = ComponentSelector.prop_select_value_first
    self.select = select

    # try to get "child" --> not a leaf node
    child = config.get(ComponentSelector.prop_single_child)
    if child is not None: 
      # try to build the child selector
      ScrapeConfigValidator.must_have_type(ComponentSelector.prop_single_child, child, dict)
      self.child = ComponentSelector(child)
      self.type = ComponentSelector.selector_type_single

      # don't do any more parsing
      return
    
    # try to get "children" --> not a leaf node
    children = config.get(ComponentSelector.prop_multi_children)
    if children is not None:
      # try to build the children selectors
      ScrapeConfigValidator.must_have_type(ComponentSelector.prop_multi_children, children, list)
      self.children = [ ComponentSelector(c) for c in children ]
      self.type = ComponentSelector.selector_type_multi
      
      # don't do any more parsing
      return

    # leaf node, try to get the extraction config
    extract = config.get(ComponentSelector.prop_extract)
    if extract is not None:
      ScrapeConfigValidator.must_have_type(ComponentSelector.prop_extract, extract, dict)
      self.extract = PropExtract(extract)
    else:
      self.extract = PropExtract() # default extract type
    
    self.type = ComponentSelector.selector_type_leaf


class PropExtract:
  """
  {
    "type": "text" | "html" | "attribute",
    | attribute:
      "key": str
  }
  """

  prop_type = "type"
  prop_type_value_text = "text"
  prop_type_value_attribute = "attribute"
  prop_type_value_html = "html"
  prop_type_values = [prop_type_value_text, prop_type_value_attribute, prop_type_value_html]

  prop_attribute_key = "key"

  def __init__(self, config: dict = {}):
    self.type = config.get(PropExtract.prop_type)
    if self.type is not None:
      ScrapeConfigValidator.must_have_type(PropExtract.prop_type, self.type, str)
      ScrapeConfigValidator.must_have_value(PropExtract.prop_type, self.type, PropExtract.prop_type_values)
    else:
      self.type = PropExtract.prop_type_value_text

    if self.type == PropExtract.prop_type_value_attribute:
      self.attribute_key: str = config.get(PropExtract.prop_attribute_key)
      ScrapeConfigValidator.must_not_be_none(PropExtract.prop_attribute_key, self.attribute_key)
      ScrapeConfigValidator.must_have_type(PropExtract.prop_attribute_key, self.attribute_key, str)

# config parsing test
if __name__ == "__main__":
  c1 = """
    {
      "pages": [
        {
          "url": "https://www.bbc.com/news/world",
          "path_patterns": [
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
          "path_patterns": [
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
          "path_patterns": [
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

  c = ConfigFactory.fromJsonString(c3)

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