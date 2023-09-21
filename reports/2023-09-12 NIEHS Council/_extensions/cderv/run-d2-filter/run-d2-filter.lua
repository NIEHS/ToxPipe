local d2FilterProg = "d2-filter"

if (os.getenv"os" or ""):match"^Windows" then
  d2FilterProg = d2FilterProg .. ".cmd"
end

function Pandoc(doc)
  return pandoc.utils.run_json_filter(doc, d2FilterProg)
end
