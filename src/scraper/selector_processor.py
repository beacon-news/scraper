from config import *
from bs4 import BeautifulSoup, Tag
import log_utils
import logging
from dateutil.parser import parse
import re

  
class SelectorProcessorException(Exception): pass

def setLogLevels(level: int):
  components = [
    SelectorProcessor,
    SingleChildSelectorProcessor,
    MultiChildSelectorProcessor,
    LeafSelectorProcessor,
    ExtractorProcessor,
    ModifierProcessor,
  ]

  for c in components:
    if getattr(c, "setLogLevel", None) is not None:
      c.setLogLevel(level)

class SelectorProcessor:

  log = log_utils.createConsoleLogger(
    name="SelectorProcessor",
    level=logging.INFO
  )

  @classmethod
  def setLogLevel(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.createConsoleLogger(
      name="SelectorProcessor",
      level=level
    )
  
  @staticmethod
  def process_html(config: ComponentSelectorConfig, html: str) -> dict | None:
    root = BeautifulSoup(html, "html.parser").select_one("html")
    if root is None:
      SelectorProcessor.log.error("no root 'html' element found")
      return None
    return SelectorProcessor.process(config, root)

  @staticmethod
  def process(config: ComponentSelectorConfig, element: Tag) -> dict | None:
    if element is None:
      return None

    # decides to select only the first, or all matches based on the 'select' config
    # delegates to a specific selector processor based on the config (single, multi, leaf)

    selector_root = SelectorProcessor._get_selector_root(config, element)

    process = {
      ComponentSelectorConfig.prop_select_value_first: {
        ComponentSelectorConfig.type_single: lambda config, x : SingleChildSelectorProcessor.select_one(config, x),
        ComponentSelectorConfig.type_multi: lambda config, x : MultiChildSelectorProcessor.select_one(config, x),
        ComponentSelectorConfig.type_leaf: lambda config, x : LeafSelectorProcessor.select_one(config, x),
      },
      ComponentSelectorConfig.prop_select_value_all: {
        ComponentSelectorConfig.type_single: lambda config, x : SingleChildSelectorProcessor.select_all(config, x),
        ComponentSelectorConfig.type_multi: lambda config, x : MultiChildSelectorProcessor.select_all(config, x),
        ComponentSelectorConfig.type_leaf: lambda config, x : LeafSelectorProcessor.select_all(config, x),
      }
    }

    try:
      res = process[config.select][config.type](config, selector_root)
    except Exception as e:
      raise SelectorProcessorException(f"failed to process: {config.select}, {config.type}", e)
    
    if res == None:
      return None

    # truncate the output to 15 characters
    SelectorProcessor.log.debug(f"setting key: {config.key}, value: {str(res)[:15]}...")

    return {
      config.key: res
    }


  @staticmethod
  def _get_selector_root(config: ComponentSelectorConfig, element: Tag) -> Tag:
    # include this element in the selector by creating a container parent div which
    # the selector will be applied to
    if config.include_self:
      SelectorProcessor.log.debug("including self, creating container div")
      container_div = BeautifulSoup("", "html.parser").new_tag("div")
      container_div.append(element)
      return container_div
    else:
      return element

  
class SingleChildSelectorProcessor:

  log = log_utils.createConsoleLogger(
    name="SingleChildSelectorProcessor",
    level=logging.INFO
  )

  @classmethod
  def setLogLevel(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.createConsoleLogger(
      name="SingleChildSelectorProcessor",
      level=level
    )

  @staticmethod
  def select_one(config: ComponentSelectorConfig, element: Tag) -> dict | None:
    SingleChildSelectorProcessor.log.debug(f"selecting one for key: {config.key}, css_selector: {config.css_selector}")

    # select the first match from the html
    elem = element.select_one(config.css_selector)
    if elem is None:
      return None
    
    return SelectorProcessor.process(config.child_selector_config, elem)
  
  @staticmethod
  def select_all(config: ComponentSelectorConfig, element: Tag) -> list | None:
    SingleChildSelectorProcessor.log.debug(f"selecting all for key: {config.key}, css_selector: {config.css_selector}")

    # select all matches from the html
    elements = element.select(config.css_selector)
    if elements is None or len(elements) == 0:
      return None
    
    results = []
    for elem in elements: 
      res = SelectorProcessor.process(config.child_selector_config, elem)
      if res is not None:
        results.append(res)

    if len(results) == 0:
      return None

    return results
    
class MultiChildSelectorProcessor:
  
  log = log_utils.createConsoleLogger(
    name="MultiChildSelectorProcessor",
    level=logging.INFO
  )

  @classmethod
  def setLogLevel(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.createConsoleLogger(
      name="MultiChildSelectorProcessor",
      level=level
    )

  @staticmethod
  def select_one(config: ComponentSelectorConfig, element: Tag) -> dict | None:
    MultiChildSelectorProcessor.log.debug(f"selecting one for key: {config.key}, css_selector: {config.css_selector}")

    elem = element.select_one(config.css_selector)
    if elem is None:
      return None

    results = []
    for c in config.child_selector_configs:
      res = SelectorProcessor.process(c, element)
      if res is not None:
        results.append(res)
    
    if len(results) == 0:
      return None
  
    return results
  
  @staticmethod
  def select_all(config: ComponentSelectorConfig, element: Tag) -> list | None:
    MultiChildSelectorProcessor.log.debug(f"selecting all for key: {config.key}, css_selector: {config.css_selector}")

    elements = element.select(config.css_selector)
    if elements is None or len(elements) == 0:
      return None
    
    results = []
    for elem in elements: 
      for c in config.child_selector_configs:
        res = SelectorProcessor.process(c, elem)
        if res is not None:
          results.append(res)

    if len(results) == 0:
      return None

    return results


class LeafSelectorProcessor:

  log = log_utils.createConsoleLogger(
    name="LeafSelectorProcessor",
    level=logging.INFO
  )

  @classmethod
  def setLogLevel(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.createConsoleLogger(
      name="LeafSelectorProcessor",
      level=level
    )

  @staticmethod
  def select_one(config: ComponentSelectorConfig, element: Tag) -> dict | None:
    LeafSelectorProcessor.log.debug(f"selecting one for key: {config.key}, css_selector: {config.css_selector}")

    # select the first match from the html
    elem = element.select_one(config.css_selector)
    if elem is None:
      return None

    # try to extract some info
    info = ExtractorProcessor.process(config.leaf_selector_config.extract, elem) 
    if info is None:
      LeafSelectorProcessor.log.debug(f"no info found for component: {config.key}, selector: {config.css_selector}, extract type: {config.leaf_selector_config.extract.type}")
    
    return info
  
  @staticmethod
  def select_all(config: ComponentSelectorConfig, element: Tag) -> list | None:
    LeafSelectorProcessor.log.debug(f"selecting all for key: {config.key}, css_selector: {config.css_selector}")

    elements = element.select(config.css_selector)
    if elements is None or len(elements) == 0:
      return None

    results = []
    for elem in elements: 
      res = ExtractorProcessor.process(config.leaf_selector_config.extract, elem)
      if res is not None:
        results.append(res)

    if len(results) == 0:
      return None

    return results


class ExtractorProcessor:

  loglevel = logging.DEBUG
  log = log_utils.createConsoleLogger(
    name="ExtractorProcessor",
    level=logging.INFO
  )

  @classmethod
  def setLogLevel(cls, level: int):
    cls.loglevel = level
    cls.log = log_utils.createConsoleLogger(
      name="ExtractorProcessor",
      level=level
    )

  @staticmethod
  def process(config: ExtractConfig, element: Tag):
    # try to process with the specific processor
    try:
      if config.type == ExtractConfig.prop_type_value_text:
        info = TextExtractorProcessor.process(element)
      elif config.type == ExtractConfig.prop_type_value_html:
        info = HtmlExtractorProcessor.process(element)
      elif config.type == ExtractConfig.prop_type_value_attribute:
        info = AttributeExtractorProcessor.process(config, element)
    except Exception as e:
      ExtractorProcessor.log.error(f"failed to process extractor: {config.type}", e)
      return None
    
    if info is None:
      return None
    
    # remove whitespace from start and end
    info = info.strip()

    for m in config.modifiers:
      try:
        info = ModifierProcessor.process(m, info)
      except Exception as e:
        ExtractorProcessor.log.error(f"failed to process modifier: {m}, error: {e}")

      if info is None:
        ExtractorProcessor.log.debug(f"no info found after modifier: {m} applied to: {info}")
        return None
    
    return info

class TextExtractorProcessor:

  @staticmethod
  def process(element: Tag) -> str | None:
    return element.text

class HtmlExtractorProcessor:

  @staticmethod
  def process(element: Tag) -> str | None:
    return str(element)

class AttributeExtractorProcessor:
  
  @staticmethod
  def process(config: ExtractConfig, element: Tag) -> str | None: 
    return element.get(config.specific_extractor_config.attribute_key)

class ModifierProcessor:

  @staticmethod
  def process(config: ModifierConfig, info: str) -> str | None:
    if config.type == ModifierConfig.prop_type_iso_date_parser:
      return IsoDateParserModifierProcessor.process(info)
    if config.type == ModifierConfig.prop_type_regex:
      return RegexModifierProcessor.process(config, info)
  
class IsoDateParserModifierProcessor:

  # additional timezone offsets
  tz_seconds = {
    "UTC": 0,
    "EST": -5 * 3600,
    "EDT": -4 * 3600,
    "CST": -6 * 3600,
    "CDT": -5 * 3600,
    "MST": -7 * 3600,
    "MDT": -6 * 3600,
    "PST": -8 * 3600,
    "PDT": -7 * 3600,
    "GMT": 0,
    "BST": 1 * 3600,
    "IST": int(5.5 * 3600),
    "CET": 1 * 3600,
    "CEST": 2 * 3600,
    "AEST": 10 * 3600,
    "AEDT": 11 * 3600,
    "ACST": int(9.5 * 3600),
    "ACDT": int(10.5 * 3600),
    "AWST": 8 * 3600
  }

  @staticmethod
  def process(info: str) -> str:
    return parse(info, fuzzy=True, tzinfos=IsoDateParserModifierProcessor.tz_seconds).isoformat()

class RegexModifierProcessor:

  @staticmethod
  def process(config: ModifierConfig, info: str) -> str:
    # extract or match based on regex 
    regex_config = config.specific_modifier_config
    for pattern in regex_config.regex:
      match = re.search(pattern, info)
      if match:
        # return the original string if any regex matches
        if regex_config.return_type == RegexModifierConfig.prop_return_original:
          return info

        # return only the first match if any regex matches
        elif regex_config.return_type == RegexModifierConfig.prop_return_first:
          return match.group(0)
        
        else:
          raise Exception(f"invalid regex modifier return type: {regex_config.return_type}")
    
    # in any other case, return None
    return None