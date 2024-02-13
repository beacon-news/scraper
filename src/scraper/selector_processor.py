from bs4 import BeautifulSoup, Tag
import logging
from config import ComponentSelector, PropExtract, PropExtractRegex, Modifier
import log_utils
import re
from dateutil.parser import parse

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

  def _extract_info_from_tag(self, prop_extract: PropExtract, tag: Tag) -> str | None:
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
    
    info = self._extract_regex(prop_extract.regex_extractor, info)


  def _extract_regex(self, prop_extract_regex: PropExtractRegex, info: str) -> str | None:
    if prop_extract_regex == None:
      return info 
    
    # extract or match based on regex from info
    for pattern in prop_extract_regex.regex:
      match = re.search(pattern, info)
      if match:
        # return the original string if any regex matches
        if prop_extract_regex.return_type == PropExtractRegex.prop_return_original:
          return info

        # return only the first match if any regex matches
        elif prop_extract_regex.return_type == PropExtractRegex.prop_return_first:
          return match.group(0)
        
      # TODO: throw error, although it shouldn't happen with proper config validation
    
    # in any other case, return None
    return None

  def _process_modifiers(self, modifiers: list[Modifier], info: str) -> str | None:
    if modifiers == None:
      return info

    # TODO: abstract away the modifiers, don't use if cases
    for m in modifiers:
      if m.type == Modifier.prop_type_iso_date_modifier:
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
        info = parse(info, fuzzy=True, tzinfos=tz_seconds).isoformat()

    return info

    