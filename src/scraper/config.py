import json
import yaml

# TODO: logging
# TODO: encourage duck typing (don't check necessarily the types of stuff, check if we're able to use them)
class ConfigValidator:

  def must_not_be_none(property: str, value):
    if value is None:
      raise ConfigValidationException(f"'{property}' field must not be None")
  
  def must_have_type(property: str, value, prop_type: object):
    if not isinstance(value, prop_type):
      raise ConfigValidationException(f"'{property}' field must be of type {prop_type}")

  def must_have_types(property: str, value, prop_types: list):
    for t in prop_types:
      if isinstance(value, t):
        return
    raise ConfigValidationException(f"'{property}' field must be one of types {prop_types}")
  
  def iterable_must_have_types(property: str, iterable_value, prop_types: list):
    for item in iterable_value:
      ConfigValidator.must_have_types(f"{property}: {item}", item, prop_types)

  def must_have_value(property: str, value, values: list):
    for v in values:
      if value == v:
        return
    raise ConfigValidationException(f"'{property}' field must be one of {values}")
  
  def must_not_be_empty(property: str, value: list):
    if len(value) == 0:
      raise ConfigValidationException(f"'{property}' field must not be empty")


class ConfigValidationException(Exception):
  pass

# TODO: every class should check its own type? (check if dict or list, don't let the parent class to do this?)
class Config:
  """
  top-level config
  {
    "version": "1.0.0",
    "pages": ScrapeConfig[]
  }
  """

  prop_version = "version"
  prop_pages = "pages"

  def __init__(self, config: dict):

    # only support version 1.0.0 for now 
    version = config.get(Config.prop_version)
    ConfigValidator.must_have_type(Config.prop_version, version, str)
    ConfigValidator.must_have_value(Config.prop_version, version, ["1.0.0"])

    scrape_config = config.get(Config.prop_pages)
    ConfigValidator.must_have_type(Config.prop_pages, scrape_config, list)
    ConfigValidator.must_not_be_empty(Config.prop_pages, scrape_config)
    self.scrape_configs: list[ScrapeConfig] = []
    for config in scrape_config:
      self.scrape_configs.append(ScrapeConfig(config))


class ConfigFactory:

  @staticmethod
  def fromJsonString(config_json_string: str) -> Config:
    return Config(json.loads(config_json_string))
  
  @staticmethod
  def fromJsonFile(path: str) -> Config:
    with open(path) as f:
      return Config(json.load(f))
  
  @staticmethod
  def fromYamlString(config_yaml_string: str) -> Config:
    return Config(yaml.safe_load(config_yaml_string))

  @staticmethod
  def fromYamlFile(path: str) -> Config:
    with open(path) as f:
      return Config(yaml.safe_load(f))


class ScrapeConfig:
  """
  scrape_config_dict format:

  {
    <optional> "metadata": dict,
    "urls": [str],
    "url_selectors": ComponentSelector,
    "selectors": ComponentSelector,
  }
  """

  prop_metadata = "metadata"
  prop_urls = "urls"
  prop_url_selectors = "url_selectors"
  prop_selectors = "selectors"

  def __init__(self, scrape_config_dict: dict):
    self.metadata = scrape_config_dict.get(ScrapeConfig.prop_metadata)
    if self.metadata is not None:
      ConfigValidator.must_have_type(ScrapeConfig.prop_metadata, self.metadata, dict)

    self.urls: str = scrape_config_dict.get(ScrapeConfig.prop_urls)
    ConfigValidator.must_have_type(ScrapeConfig.prop_urls, self.urls, list)
    ConfigValidator.must_not_be_empty(ScrapeConfig.prop_urls, self.urls)
    ConfigValidator.iterable_must_have_types(ScrapeConfig.prop_urls, self.urls, [str])

    url_selectors = scrape_config_dict.get(ScrapeConfig.prop_url_selectors)
    ConfigValidator.must_not_be_none(ScrapeConfig.prop_url_selectors, url_selectors)
    ConfigValidator.must_not_be_empty(ScrapeConfig.prop_url_selectors, url_selectors)
    ConfigValidator.must_have_type(ScrapeConfig.prop_url_selectors, url_selectors, dict) 
    self.url_selectors = ComponentSelector(url_selectors)

    selectors = scrape_config_dict.get(ScrapeConfig.prop_selectors)
    ConfigValidator.must_have_type(ScrapeConfig.prop_selectors, selectors, dict)
    self.selectors = ComponentSelector(selectors)

class ComponentSelector:
  """
  'single'
  {
    "key": str,
    "selector": str,
    "select": "first" | "all",
    <optional> "include_self": "true",
    "child": ComponentSelector
  }
  'multi'
  {
    "key": str,
    "selector": str,
    "select": "first" | "all",
    <optional> "include_self": "true",
    "children": ComponentSelector[] 
  }
  'leaf'
  {
    "key": str,
    "selector": str,
    "select": "first" | "all",
    <optional> "include_self": "true",
    "extract": PropExtract
  }
  """

  prop_key = "key"
  prop_css_selector = "selector"

  prop_include_self = "include_self"
  prop_include_self_value_true = "true"
  
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
    ConfigValidator.must_have_type(ComponentSelector.prop_key, self.key, str)

    # selector can be empty, select everything by default then
    css_selector = config.get(ComponentSelector.prop_css_selector)
    if css_selector is not None:
      ConfigValidator.must_have_type(ComponentSelector.prop_css_selector, css_selector, str) 
    else:
      css_selector = "*"
    self.css_selector = css_selector 

    # select mode can be empty
    select = config.get(ComponentSelector.prop_select)
    if select is not None:
      ConfigValidator.must_have_type(ComponentSelector.prop_select, select, str)
      ConfigValidator.must_have_value(ComponentSelector.prop_select, select, ComponentSelector.prop_select_values)
    else:
      select = ComponentSelector.prop_select_value_first
    self.select = select

    # include_self can be empty -> false by default
    # controls if the selector also includes the element itself instead of only its children
    include_self = config.get(ComponentSelector.prop_include_self)
    if include_self is not None:
      ConfigValidator.must_have_types(ComponentSelector.prop_include_self, include_self, [str, bool])
      ConfigValidator.must_have_value(
        ComponentSelector.prop_include_self, 
        include_self, 
        [ComponentSelector.prop_include_self_value_true, True]
      )
    self.include_self = True if include_self == True or include_self == ComponentSelector.prop_include_self_value_true else False

    # try to get "child" --> not a leaf node
    child = config.get(ComponentSelector.prop_single_child)
    if child is not None: 
      # try to build the child selector
      ConfigValidator.must_have_type(ComponentSelector.prop_single_child, child, dict)
      self.child = ComponentSelector(child)
      self.type = ComponentSelector.selector_type_single

      # don't do any more parsing
      return
    
    # try to get "children" --> not a leaf node
    children = config.get(ComponentSelector.prop_multi_children)
    if children is not None:
      # try to build the children selectors
      ConfigValidator.must_have_type(ComponentSelector.prop_multi_children, children, list)
      self.children = [ ComponentSelector(c) for c in children ]
      self.type = ComponentSelector.selector_type_multi
      
      # don't do any more parsing
      return

    # leaf node
    self.type = ComponentSelector.selector_type_leaf

    # try to get the extraction config
    extract = config.get(ComponentSelector.prop_extract)
    if extract is not None:
      ConfigValidator.must_have_type(ComponentSelector.prop_extract, extract, dict)
      self.extract = PropExtract(extract)
    else:
      self.extract = PropExtract() # default extract type


class PropExtract:
  """
  {
    "type": "text" | "html" | "attribute",
    | attribute:
      "key": str
    <optional> "regex": PropExtractRegex
    <optional> "modifiers": [Modifier]
  }
  """

  prop_type = "type"
  prop_type_value_text = "text"
  prop_type_value_attribute = "attribute"
  prop_type_value_html = "html"
  prop_type_values = [prop_type_value_text, prop_type_value_attribute, prop_type_value_html]

  prop_attribute_key = "key"
  # prop_regex_extractor = "regex_extractor"
  prop_modifiers = "modifiers"

  def __init__(self, config: dict = {}):
    self.type = config.get(PropExtract.prop_type)
    if self.type is not None:
      ConfigValidator.must_have_type(PropExtract.prop_type, self.type, str)
      ConfigValidator.must_have_value(PropExtract.prop_type, self.type, PropExtract.prop_type_values)
    else:
      self.type = PropExtract.prop_type_value_text

    if self.type == PropExtract.prop_type_value_attribute:
      self.attribute_key: str = config.get(PropExtract.prop_attribute_key)
      ConfigValidator.must_have_type(PropExtract.prop_attribute_key, self.attribute_key, str)
    
    modifiers = config.get(PropExtract.prop_modifiers)
    if modifiers is not None:
      ConfigValidator.must_have_type(PropExtract.prop_modifiers, modifiers, list)
      ConfigValidator.must_not_be_empty(PropExtract.prop_modifiers, modifiers)
      self.modifiers = [ Modifier(m) for m in modifiers ]
    else:
      self.modifiers = None
  
class Modifier:
  """
  {
    "type": "iso_date_parser" | "regex",
  }
  """
  prop_type = "type"
  prop_type_iso_date_parser = "iso_date_parser"
  prop_type_regex = "regex"
  prop_type_values = [prop_type_iso_date_parser, prop_type_regex]

  def __init__(self, config: dict):
    self.type = config.get(Modifier.prop_type)
    ConfigValidator.must_have_type(Modifier.prop_type, self.type, str)
    ConfigValidator.must_have_value(Modifier.prop_type, self.type, Modifier.prop_type_values)
  
    if self.type == Modifier.prop_type_iso_date_parser:
      self.specific_modifier = IsoDateParserModifier()
    elif self.type == Modifier.prop_type_regex:
      self.specific_modifier = RegexModifier(config)

class IsoDateParserModifier: pass

class RegexModifier: 
  prop_regex = "regex"
  prop_return = "return"
  prop_return_original = "original"
  prop_return_first = "first"
  prop_return_values = [prop_return_original, prop_return_first]

  def __init__(self, config: dict):
    self.regex = config.get(RegexModifier.prop_regex)
    ConfigValidator.must_have_type(RegexModifier.prop_regex, self.regex, list)
    ConfigValidator.must_not_be_empty(RegexModifier.prop_regex, self.regex)
    ConfigValidator.iterable_must_have_types(RegexModifier.prop_regex, self.regex, [str])

    self.return_type = config.get(RegexModifier.prop_return)
    if self.return_type is not None:
      ConfigValidator.must_have_type(RegexModifier.prop_return, self.return_type, str)
      ConfigValidator.must_have_value(RegexModifier.prop_return, self.return_type, RegexModifier.prop_return_values)
    else:
      # by default return the original string
      self.return_type = RegexModifier.prop_return_original
