import json
import yaml
import jsonpath_ng.ext as jsonpath_ng_ext


# TODO: use pydantic models instead of implementing the same thing, but worse... 
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
    "pages": ScrapeConfig[],
    <optional> "common_selectors": CommonComponentSelectorsConfig,
  }
  """

  prop_version = "version"
  prop_pages = "pages"
  prop_common_selectors = "common_selectors"

  def __init__(self, config: dict, file_path: str = None):

    # set the path to the config file
    self.file_path = file_path

    # version
    # only support version 1.0.0 for now 
    version = config.get(Config.prop_version)
    ConfigValidator.must_have_type(Config.prop_version, version, str)
    ConfigValidator.must_have_value(Config.prop_version, version, ["1.0.0"])

    # scrape configs
    scrape_config = config.get(Config.prop_pages)
    ConfigValidator.must_have_type(Config.prop_pages, scrape_config, list)
    ConfigValidator.must_not_be_empty(Config.prop_pages, scrape_config)
    self.scrape_configs: list[ScrapeConfig] = []
    for sc in scrape_config:
      self.scrape_configs.append(ScrapeConfig(sc))

    # common selectors dict
    common_selectors = config.get(Config.prop_common_selectors)
    if common_selectors is not None:
      ConfigValidator.must_have_type(Config.prop_common_selectors, common_selectors, list)
      ConfigValidator.must_not_be_empty(Config.prop_common_selectors, common_selectors)
      ConfigValidator.iterable_must_have_types(Config.prop_common_selectors, common_selectors, [dict])
    else:
      common_selectors = []
    self.common_selectors = CommonComponentSelectorsConfig(common_selectors)
    print(self.common_selectors.common_selectors)

    # check for loops after initializing everything
    for sc in self.scrape_configs:
      self.check_loops(sc.selectors)
  
  def check_loops(self, s, visited = set()):

    if s.type == ComponentSelectorConfig.type_ref:
      name = s.common_selector
      next = self.common_selectors.common_selectors[s.common_selector]
    elif s.type == ComponentSelectorConfig.type_single:
      name = s.key
      next = s.child_selector_config
    elif s.type == ComponentSelectorConfig.type_leaf:
      # leaf nodes don't refer to other selectors, it's allowed to reach them from multiple paths
      return
    elif s.type == ComponentSelectorConfig.type_multi:
      for next in s.child_selector_configs:
        self.check_loops(next, visited) 
      return

    if s in visited:
      raise ConfigValidationException(f"selector loop detected: {name}") 
    visited.add(s)
    self.check_loops(next, visited)

class ConfigFactory:

  @staticmethod
  def from_file(config_path: str) -> Config:
    if config_path.endswith(".json"):
      return ConfigFactory.from_json_file(config_path)
    elif config_path.endswith(".yaml"):
      return ConfigFactory.from_yaml_file(config_path)
    else:
      raise Exception(f"config file must be json or yaml, provided: '{config_path}'")

  @staticmethod
  def from_json_str(config_json_string: str) -> Config:
    return Config(json.loads(config_json_string))
  
  @staticmethod
  def from_json_file(path: str) -> Config:
    with open(path) as f:
      return Config(json.load(f), path)
  
  @staticmethod
  def from_yaml_str(config_yaml_string: str) -> Config:
    return Config(yaml.safe_load(config_yaml_string))

  @staticmethod
  def from_yaml_file(path: str) -> Config:
    with open(path) as f:
      return Config(yaml.safe_load(f), path)
  

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
    # metadata
    self.metadata = scrape_config_dict.get(ScrapeConfig.prop_metadata)
    if self.metadata is not None:
      ConfigValidator.must_have_type(ScrapeConfig.prop_metadata, self.metadata, dict)

    # urls
    self.urls: str = scrape_config_dict.get(ScrapeConfig.prop_urls)
    ConfigValidator.must_have_type(ScrapeConfig.prop_urls, self.urls, list)
    ConfigValidator.must_not_be_empty(ScrapeConfig.prop_urls, self.urls)
    ConfigValidator.iterable_must_have_types(ScrapeConfig.prop_urls, self.urls, [str])

    # url selectors
    url_selectors = scrape_config_dict.get(ScrapeConfig.prop_url_selectors)
    ConfigValidator.must_not_be_none(ScrapeConfig.prop_url_selectors, url_selectors)
    ConfigValidator.must_not_be_empty(ScrapeConfig.prop_url_selectors, url_selectors)
    ConfigValidator.must_have_type(ScrapeConfig.prop_url_selectors, url_selectors, dict) 
    self.url_selectors = ComponentSelectorConfig(url_selectors)

    # selectors object
    selectors = scrape_config_dict.get(ScrapeConfig.prop_selectors)
    ConfigValidator.must_have_type(ScrapeConfig.prop_selectors, selectors, dict)
    self.selectors = ComponentSelectorConfig(selectors)


class CommonComponentSelectorsConfig:
  """
  maintains a dict of common component selectors
  """

  def __init__(self, configs: list[dict]):

    self.common_selectors = {}
    for config in configs:
      common_selector = CommonComponentSelectorConfig(config) 
      self.common_selectors[common_selector.name] = common_selector.selector
    

class CommonComponentSelectorConfig:
  """
  common selector dict format, can be used by selectors with referring to the 'name'
  {
    "name": str,
    "selector": ComponentSelectorConfig
  }
  """

  prop_name = "name"
  prop_selector = "selector"

  def __init__(self, config: dict):
    self.name: str = config.get(CommonComponentSelectorConfig.prop_name)
    ConfigValidator.must_have_type(CommonComponentSelectorConfig.prop_name, self.name, str)

    selector = config.get(CommonComponentSelectorConfig.prop_selector)
    ConfigValidator.must_not_be_none(CommonComponentSelectorConfig.prop_selector, selector)
    ConfigValidator.must_have_type(CommonComponentSelectorConfig.prop_selector, selector, dict)
    self.selector = ComponentSelectorConfig(selector)


class ComponentSelectorConfig:
  """
  {
    "common_selector": str,
    ---------------------------- OR (common_selector's presence refers to a common selector, ignoring other attributes) 
    "key": str,
    "selector": str,
    "select": "first" | "all",
    <optional> "include_self": "true",
    | "child": ComponentSelectorConfig | ComponentSelectorConfig + LeafComponentSelectorConfig,
    | "children": [ComponentSelectorConfig],
  }

  This class contains the common parts for the selector types.
  """
  # if present, it refers to a common selector and all other attributes are ignored
  prop_common_selector = "common_selector" 

  # common props for most selector types
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

  # selector type
  type_single = 0 
  type_multi = 1
  type_leaf = 2
  type_ref = 3 # reference to a common selector

  def __init__(self, config: dict):

    # common selector can be empty
    common_selector = config.get(ComponentSelectorConfig.prop_common_selector)
    if (common_selector is not None):
      # if this selector is only a reference to a common selector, store the reference and return
      ConfigValidator.must_have_type(ComponentSelectorConfig.prop_common_selector, common_selector, str) 
      self.type = ComponentSelectorConfig.type_ref
      self.common_selector = common_selector
      return
    else:
      self.common_selector = None

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
      self.type = self.type_single
      self.child_selector_config = ComponentSelectorConfig(child) 
      # don't do any more parsing in this case
      return

    # try to get "children" --> not a leaf node
    children = config.get(ComponentSelectorConfig.prop_multi_children)
    if children is not None:
      ConfigValidator.must_have_type(ComponentSelectorConfig.prop_multi_children, children, list)
      self.type = self.type_multi
      self.child_selector_configs = [ ComponentSelectorConfig(c) for c in children ]
      # don't do any more parsing in this case
      return
    
    # leaf node
    self.type = self.type_leaf
    self.leaf_selector_config = LeafComponentSelectorConfig(config)


class LeafComponentSelectorConfig:
  """
  ComponentSelectorConfig | 
  {
    "extract": ExtractConfig
    <optional> "modifiers": [Modifier]
  }
  This class contains the specific parts for the "leaf" selector type.
  """
  
  prop_extract = "extract"
  prop_modifiers = "modifiers"

  def __init__(self, config: dict):

    # try to get the extraction config
    extract = config.get(LeafComponentSelectorConfig.prop_extract)
    if extract is not None:
      ConfigValidator.must_have_type(LeafComponentSelectorConfig.prop_extract, extract, dict)
      self.extract = ExtractConfig(extract)
    else:
      self.extract = ExtractConfig() # default extract type

    # create the modifier configs
    modifiers = config.get(LeafComponentSelectorConfig.prop_modifiers)
    if modifiers is not None:
      ConfigValidator.must_have_type(LeafComponentSelectorConfig.prop_modifiers, modifiers, list)
      ConfigValidator.must_not_be_empty(LeafComponentSelectorConfig.prop_modifiers, modifiers)
      self.modifiers = [ ModifierConfig(m) for m in modifiers ]
    else:
      self.modifiers = []


class ExtractConfig:
  """
  {
    "type": "text" | "html" | "attribute" | "jsonpath",
  }
  This class contains the common parts for the extractor types.
  """
  # common props for all extract types
  prop_type = "type"
  prop_type_value_text = "text"
  prop_type_value_attribute = "attribute"
  prop_type_value_html = "html"
  prop_type_value_jsonpath = "jsonpath"
  prop_type_values = [
    prop_type_value_text, 
    prop_type_value_attribute,
    prop_type_value_html,
    prop_type_value_jsonpath
  ]


  def __init__(self, config: dict = {}):
    # try to get the type, extract text by default
    self.type = config.get(ExtractConfig.prop_type)
    if self.type is not None:
      ConfigValidator.must_have_type(ExtractConfig.prop_type, self.type, str)
      ConfigValidator.must_have_value(ExtractConfig.prop_type, self.type, ExtractConfig.prop_type_values)
    else:
      self.type = ExtractConfig.prop_type_value_text

    # create the specific extractor config
    # don't create a specific extractor if it doesn't have any additional configs, it would be an empty class
    # so don't create specific extractor for text and html
    if self.type == ExtractConfig.prop_type_value_attribute:
      self.specific_extractor_config = AttributeExtractConfig(config)
    elif self.type == ExtractConfig.prop_type_value_jsonpath:
      self.specific_extractor_config = JsonpathExtractConfig(config)


class AttributeExtractConfig:
  """
  ExtractConfig | 
  {
    "key": str,
  }
  This class contains the specific parts for the "attribute" extractor type.
  """
  prop_attribute_key = "key"

  def __init__(self, config: dict):
    self.attribute_key = config.get(AttributeExtractConfig.prop_attribute_key)
    ConfigValidator.must_have_type(AttributeExtractConfig.prop_attribute_key, self.attribute_key, str)

class JsonpathExtractConfig:
  """
  ExtractConfig | 
  {
    "path": str,
  }
  This class contains the specific parts for the "jsonpath" extractor type.
  """
  prop_jsonpath_path = "path"

  def __init__(self, config: dict):
    self.jsonpath_path = config.get(JsonpathExtractConfig.prop_jsonpath_path)
    ConfigValidator.must_have_type(JsonpathExtractConfig.prop_jsonpath_path, self.jsonpath_path, str)

    # create and store the expression here
    self.jsonpath_expr = jsonpath_ng_ext.parse(self.jsonpath_path)
  
class ModifierConfig:
  """
  {
    "type": "iso_date_parser" | "regex",
  }
  This class contains the common parts for the modifier types.
  """
  prop_type = "type"
  prop_type_iso_date_parser = "iso_date_parser"
  prop_type_regex = "regex"
  prop_type_values = [prop_type_iso_date_parser, prop_type_regex]

  def __init__(self, config: dict):
    self.type = config.get(ModifierConfig.prop_type)
    ConfigValidator.must_have_type(ModifierConfig.prop_type, self.type, str)
    ConfigValidator.must_have_value(ModifierConfig.prop_type, self.type, ModifierConfig.prop_type_values)
  
    # only create specific modifier for types which have additional configs
    # iso_date_parser would be and empty class, so don't create an object for it
    if self.type == ModifierConfig.prop_type_regex:
      self.specific_modifier_config = RegexModifierConfig(config)

class RegexModifierConfig: 
  """
  ModifierConfig | 
  {
    "return": "original" | "first",
    "regex": [str],
  }
  This class contains the specific parts for the "regex" modifier type.
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
