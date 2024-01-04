from bs4 import BeautifulSoup, Tag
import logging
from config import PropExtract, ComponentSelector
import log_utils

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

  def _extract_info_from_tag(self, propExtract: PropExtract, tag: Tag) -> str | None:
    info = None
    if propExtract.type == PropExtract.prop_type_value_text:
      info = tag.text
    elif propExtract.type == PropExtract.prop_type_value_html:
      info = str(tag)
    elif propExtract.type == PropExtract.prop_type_value_attribute:
      info = tag.get(propExtract.attribute_key)
    
    if len(info) == 0:
      return None
  
    info = info.strip()
      
    return info
    