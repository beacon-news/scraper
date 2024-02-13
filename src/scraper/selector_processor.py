from bs4 import BeautifulSoup, Tag
import logging
from config import ComponentSelector, PropExtract, PropExtractRegex
import log_utils
import re

class SelectorProcessor:

  def __init__(self, loglevel: int = logging.INFO):
    self.log = log_utils.createConsoleLogger(
      name=self.__class__.__name__,
      level=loglevel,
    )

  def process(self, selector: ComponentSelector, html: str) -> dict | None:
    root = BeautifulSoup(html, "html.parser").select_one("html")
    if root is None:
      self.log.error("no root 'html' element found")
      return None

    return self._process_selectors(selector, root)
    
  def _process_selectors(self, selector: ComponentSelector, element: Tag) -> dict | None:
    if selector.select == ComponentSelector.prop_select_value_first:
      return self._process_selectors_one(selector, element)
    elif selector.select == ComponentSelector.prop_select_value_all:
      return self._process_selectors_more(selector, element)

  # TODO: keep the order of items when a selector has more children
  def _process_selectors_one(self, selector: ComponentSelector, element: Tag) -> dict | None:
    result = {}

    select_root = self._get_selector_root(selector, element)
    elem = select_root.select_one(selector.css_selector)
    if elem is None:
      self.log.debug(f"no element found for component {selector.key}, selector: {selector.css_selector}")
      return None
    
    if selector.type == ComponentSelector.selector_type_leaf:
      # try to extract some info
      info = self._extract_info_from_tag(selector.extract, elem)
      if info is None:
        self.log.debug(f"no info found for component: {selector.key}, selector: {selector.css_selector}, extract type: {selector.extract.type}")
        return None
      else:
        result[selector.key] = info
    
    elif selector.type == ComponentSelector.selector_type_single:
      res = self._process_selectors(selector.child, elem)
      if res is None:
        return None
      result[selector.key] = res

    elif selector.type == ComponentSelector.selector_type_multi:
      result_list = []
      for s in selector.children:
        res = self._process_selectors(s, elem)
        if res is not None:
          result_list.append(res)

      if len(result_list) == 0:
        return None

      result[selector.key] = result_list
    
    return result

  # TODO: keep the order of items when a selector has more children
  def _process_selectors_more(self, selector: ComponentSelector, element: Tag) -> dict | None:
    result = {}
    result_list = []

    select_root = self._get_selector_root(selector, element)
    elems = select_root.select(selector.css_selector)
    if len(elems) == 0:
      self.log.debug(f"no elements found for component {selector.key}, selector: {selector.css_selector}")
      return None
    
    if selector.type == ComponentSelector.selector_type_leaf:
      for elem in elems:
        # try to extract some info
        info = self._extract_info_from_tag(selector.extract, elem)
        if info is None:
          self.log.debug(f"no info found for component: {selector.key}, selector: {selector.css_selector}, extract type: {selector.extract.type}")
        else:
          result_list.append(info)

    elif selector.type == ComponentSelector.selector_type_single:
      for elem in elems:
        res = self._process_selectors(selector.child, elem)
        if res is not None:
          result_list.append(res)

    elif selector.type == ComponentSelector.selector_type_multi:
      for elem in elems:
        for s in selector.children:
          res = self._process_selectors(s, elem)
          if res is not None:
            result_list.append(res)

    if len(result_list) == 0:
      return None

    result[selector.key] = result_list
    return result

  def _get_selector_root(self, selector: ComponentSelector, element: Tag) -> Tag:
    # include this element in the selector by creating a container parent div which
    # the selector will be applied to
    if selector.include_self:
      self.log.debug("including self, creating container div")
      container_div = BeautifulSoup("", "html.parser").new_tag("div")
      container_div.append(element)
      return container_div
    else:
      return element

  def _extract_info_from_tag(self, prop_extract: PropExtract, tag: Tag) -> str | list[str] | None:
    info = None
    if prop_extract.type == PropExtract.prop_type_value_text:
      info = tag.text
    elif prop_extract.type == PropExtract.prop_type_value_html:
      info = str(tag)
    elif prop_extract.type == PropExtract.prop_type_value_attribute:
      info = tag.get(prop_extract.attribute_key)
    
    if info == None or len(info) == 0:
      return None
    
    info = info.strip()
    
    if prop_extract.regex_extractor == None:
      return info 
    
    # extract or match based on regex from info
    extractor = prop_extract.regex_extractor

    # return the original string if any regex matches
    if extractor.return_type == PropExtractRegex.prop_return_original: 
      for pattern in extractor.regex:
        if re.search(pattern, info):
          return info
      
    # return only the first match if any regex matches
    elif extractor.return_type == PropExtractRegex.prop_return_first:
      for pattern in extractor.regex:
        match = re.search(pattern, info)
        if match:
          return match.group(0)
    
    # in any other case, return None
    return None

    