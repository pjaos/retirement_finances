function Link(el)
  local target = el.target
  -- Match links like "something.md#anchor"
  local base, anchor = target:match("([^#]+)%.md#(.+)")
  if base and anchor then
    el.target = "#" .. anchor
    return el
  end

  -- Match links like "something.md"
  local md_only = target:match("([^#]+)%.md$")
  if md_only then
    -- Strip the .md; leave as plain text or maybe remove entirely
    el.target = ""
    return el
  end

  return el
end