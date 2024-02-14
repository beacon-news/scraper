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
    self.url_selectors = ComponentSelectorConfig(url_selectors)

    selectors = scrape_config_dict.get(ScrapeConfig.prop_selectors)
    ConfigValidator.must_have_type(ScrapeConfig.prop_selectors, selectors, dict)
    self.selectors = ComponentSelectorConfig(selectors)

class ComponentSelectorConfig:
  """
  {
    "key": str,
    "selector": str,
    "select": "first" | "all",
    <optional> "include_self": "true",
    "child" | "children": SingleChildComponentSelectorConfig | MultiChildComponentSelectorConfig
  }
  """
  # common props for all selector types
  prop_key = "key"
  prop_css_selector = "selector"

  prop_include_self = "include_self"
  prop_include_self_value_true = "true"
  
  prop_select = "select"
  prop_select_value_first = "first"
  prop_select_value_all = "all"
  prop_select_values = [prop_select_value_first, prop_select_value_all]

  # to decide which specific selector to create
  prop_single_child = "child"
  prop_multi_children = "children"

  def __init__(self, config: dict):
    # key is mandatory
    self.key = config.get(ComponentSelectorConfig.prop_key)
    ConfigValidator.must_have_type(ComponentSelectorConfig.prop_key, self.key, str)

    # selector can be empty, select everything by default then
    css_selector = config.get(ComponentSelectorConfig.prop_css_selector)
    if css_selector is not None:
      ConfigValidator.must_have_type(ComponentSelectorConfig.prop_css_selector, css_selector, str) 
    else:
      css_selector = "*"
    self.css_selector = css_selector 

    # select mode can be empty, select first by default
    select = config.get(ComponentSelectorConfig.prop_select)
    if select is not None:
      ConfigValidator.must_have_type(ComponentSelectorConfig.prop_select, select, str)
      ConfigValidator.must_have_value(ComponentSelectorConfig.prop_select, select, ComponentSelectorConfig.prop_select_values)
    else:
      select = ComponentSelectorConfig.prop_select_value_first
    self.select = select

    # include_self can be empty, false by default
    # controls if the selector also includes the element itself instead of only its children
    include_self = config.get(ComponentSelectorConfig.prop_include_self)
    if include_self is not None:
      ConfigValidator.must_have_types(ComponentSelectorConfig.prop_include_self, include_self, [str, bool])
      ConfigValidator.must_have_value(
        ComponentSelectorConfig.prop_include_self, 
        include_self, 
        [ComponentSelectorConfig.prop_include_self_value_true, True]
      )
    self.include_self = True if include_self == True or include_self == ComponentSelectorConfig.prop_include_self_value_true else False

    # try to get "child" --> not a leaf node
    child = config.get(ComponentSelectorConfig.prop_single_child)
    if child is not None: 
      self.specific_selector = SingleChildComponentSelectorConfig(child)

    # try to get "children" --> not a leaf node
    children = config.get(ComponentSelectorConfig.prop_multi_children)
    if children is not None:
      ConfigValidator.must_have_type(ComponentSelectorConfig.prop_multi_children, children, list)
      self.specific_selector = MultiChildComponentSelectorConfig(children)
    
    # leaf node
    self.specific_selector = LeafComponentSelectorConfig(config)

class SingleChildComponentSelectorConfig(ComponentSelectorConfig):
  """
  {
    "key": str,
    "selector": str,
    "select": "first" | "all",
    <optional> "include_self": "true",
    "child": ComponentSelectorConfig,
  }
  """
  def __init__(self, config: dict):
    self.selector = ComponentSelectorConfig(config)


class MultiChildComponentSelectorConfig(ComponentSelectorConfig):
  """
  {
    "key": str,
    "selector": str,
    "select": "first" | "all",
    <optional> "include_self": "true",
    "children": [ComponentSelectorConfig],
  }
  """

  def __init__(self, config: list):
    self.selectors = [ ComponentSelectorConfig(c) for c in config ]

    
class LeafComponentSelectorConfig(ComponentSelectorConfig):
  """
  {
    "key": str,
    "selector": str,
    "select": "first" | "all",
    <optional> "include_self": "true",
    "extract": ExtractConfig
  }
  """
  
  prop_extract = "extract"

  def __init__(self, config: dict):

    # try to get the extraction config
    extract = config.get(LeafComponentSelectorConfig.prop_extract)
    if extract is not None:
      ConfigValidator.must_have_type(LeafComponentSelectorConfig.prop_extract, extract, dict)
      self.extract = ExtractConfig(extract)
    else:
      self.extract = ExtractConfig() # default extract type


class ExtractConfig:
  """
  {
    "type": "text" | "html" | "attribute",
    <optional> "modifiers": [Modifier]
  }
  """
  # common props for all extract types
  prop_type = "type"
  prop_type_value_text = "text"
  prop_type_value_attribute = "attribute"
  prop_type_value_html = "html"
  prop_type_values = [prop_type_value_text, prop_type_value_attribute, prop_type_value_html]

  prop_modifiers = "modifiers"

  def __init__(self, config: dict = {}):
    # try to get the type, extract text by default
    self.type = config.get(ExtractConfig.prop_type)
    if self.type is not None:
      ConfigValidator.must_have_type(ExtractConfig.prop_type, self.type, str)
      ConfigValidator.must_have_value(ExtractConfig.prop_type, self.type, ExtractConfig.prop_type_values)
    else:
      self.type = ExtractConfig.prop_type_value_text

    # create the specific extractor config
    if self.type == ExtractConfig.prop_type_value_text:
      self.specific_extractor = TextExtractConfig()
    elif self.type == ExtractConfig.prop_type_value_html:
      self.specific_extractor = HtmlExtractConfig()
    elif self.type == ExtractConfig.prop_type_value_attribute:
      self.specific_extractor = AttributeExtractConfig(config)

    # create the modifier configs
    modifiers = config.get(ExtractConfig.prop_modifiers)
    if modifiers is not None:
      ConfigValidator.must_have_type(ExtractConfig.prop_modifiers, modifiers, list)
      ConfigValidator.must_not_be_empty(ExtractConfig.prop_modifiers, modifiers)
      self.modifiers = [ ModifierConfig(m) for m in modifiers ]
    else:
      self.modifiers = None


class TextExtractConfig(ExtractConfig):
  """
  {
    "type": "text",
    <optional> "modifiers": [Modifier]
  }
  """
  def __init__(self): pass

class HtmlExtractConfig(ExtractConfig): 
  """
  {
    "type": "html",
    <optional> "modifiers": [Modifier]
  }
  """
  def __init__(self): pass

class AttributeExtractConfig(ExtractConfig):
  """
  {
    "type": "attribute",
    "key": str,
    <optional> "modifiers": [Modifier]
  }
  """
  prop_attribute_key = "key"

  def __init__(self, config: dict):
    super().__init__(config)
    self.attribute_key = config.get(AttributeExtractConfig.prop_attribute_key)
    ConfigValidator.must_have_type(AttributeExtractConfig.prop_attribute_key, self.attribute_key, str)
  
class ModifierConfig:
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
    self.type = config.get(ModifierConfig.prop_type)
    ConfigValidator.must_have_type(ModifierConfig.prop_type, self.type, str)
    ConfigValidator.must_have_value(ModifierConfig.prop_type, self.type, ModifierConfig.prop_type_values)
  
    if self.type == ModifierConfig.prop_type_iso_date_parser:
      self.specific_modifier = IsoDateParserModifierConfig()
    elif self.type == ModifierConfig.prop_type_regex:
      self.specific_modifier = RegexModifierConfig(config)

class IsoDateParserModifierConfig: 
  """
  {
    "type": "iso_date_parser"
  }
  """
  pass

class RegexModifierConfig: 
  """
  {
    "type": "regex",
    "return": "original" | "first",
    "regex": [str],
  }
  """
  prop_regex = "regex"
  prop_return = "return"
  prop_return_original = "original"
  prop_return_first = "first"
  prop_return_values = [prop_return_original, prop_return_first]

  def __init__(self, config: dict):
    self.regex = config.get(RegexModifierConfig.prop_regex)
    ConfigValidator.must_have_type(RegexModifierConfig.prop_regex, self.regex, list)
    ConfigValidator.must_not_be_empty(RegexModifierConfig.prop_regex, self.regex)
    ConfigValidator.iterable_must_have_types(RegexModifierConfig.prop_regex, self.regex, [str])

    self.return_type = config.get(RegexModifierConfig.prop_return)
    if self.return_type is not None:
      ConfigValidator.must_have_type(RegexModifierConfig.prop_return, self.return_type, str)
      ConfigValidator.must_have_value(RegexModifierConfig.prop_return, self.return_type, RegexModifierConfig.prop_return_values)
    else:
      # by default return the original string
      self.return_type = RegexModifierConfig.prop_return_original

