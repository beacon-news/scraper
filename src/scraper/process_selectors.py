from bs4 import BeautifulSoup, Tag
import logging
from config import ScrapeConfig, PropExtract, ComponentSelector


logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def extract_info_from_tag(tag: Tag, propExtract: PropExtract) -> str | None:
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

# TODO: keep the order of items when a selector has more children

def process_selectors_one(selector: ComponentSelector, element: Tag) -> dict | None:
  result = {}

  # only select the first one
  elem = element.select_one(selector.css_selector)
  if elem is None:
    log.debug(f"no element found for component {selector.key}, selector: {selector.css_selector}")
    return None
  
  if selector.type == ComponentSelector.selector_type_leaf:
    # try to extract some info
    info = extract_info_from_tag(elem, selector.extract)
    if info is None:
      log.debug(f"no info found for component: {selector.key}, selector: {selector.css_selector}, extract type: {selector.extract.type}")
      return None
    else:
      result[selector.key] = info
  
  elif selector.type == ComponentSelector.selector_type_single:
    res = process_selectors(selector.child, elem)
    if res is None:
      return None
    result[selector.key] = res

  elif selector.type == ComponentSelector.selector_type_multi:
    result_list = []
    for s in selector.children:
      res = process_selectors(s, elem)
      if res is not None:
        result_list.append(res)

    if len(result_list) == 0:
      return None
    result[selector.key] = result_list
   
  return result

def process_selectors_more(selector: ComponentSelector, element: Tag) -> dict | None:
  result = {}
  result_list = []

  elems = element.select(selector.css_selector)
  if len(elems) == 0:
    log.debug(f"no elements found for component {selector.key}, selector: {selector.css_selector}")
    return None
  
  if selector.type == ComponentSelector.selector_type_leaf:
    for elem in elems:
      # try to extract some info
      info = extract_info_from_tag(elem, selector.extract)
      if info is None:
        log.debug(f"no info found for component: {selector.key}, selector: {selector.css_selector}, extract type: {selector.extract.type}")
      else:
        result_list.append(info)

  elif selector.type == ComponentSelector.selector_type_single:
    for elem in elems:
      res = process_selectors(selector.child, elem)
      if res is not None:
        result_list.append(res)

  elif selector.type == ComponentSelector.selector_type_multi:
    for elem in elems:
      for s in selector.children:
        res = process_selectors(s, elem)
        if res is not None:
          result_list.append(res)

  if len(result_list) == 0:
    return None

  result[selector.key] = result_list
  return result


def process_selectors(selector: ComponentSelector, element: Tag) -> dict | None:
  if selector.select == ComponentSelector.prop_select_value_first:
    return process_selectors_one(selector, element)
  elif selector.select == ComponentSelector.prop_select_value_all:
    return process_selectors_more(selector, element)


def process_from_root(scrape_config: ScrapeConfig, soup: BeautifulSoup) -> dict | None:
  root = soup.select_one("html")
  if root is None:
    log.error(f"no root 'html' element found")
    return None

  return process_selectors(scrape_config.selectors, root)