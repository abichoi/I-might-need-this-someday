# I-might-need-this-someday
A place for me to store websites where I might find it useful someday

## Browsing and adding links

- **Search page:** https://abichoi.github.io/I-might-need-this-someday/ (served by GitHub Pages from `index.html`)
- **Add / edit / delete (owner only):** click *Owner sign-in* at the bottom of the page and paste a fine-grained
  GitHub token scoped to this repo with *Contents: Read and write*. The token stays in that browser only.
  Then use **+ Add link**, or **Edit** on any entry; changes are committed straight to `links.yml`.
  Visitors can only view and search.
- **Via an issue:** an issue titled `Add link: …` with a YAML block, opened by the owner, is added by the
  `Add link from issue` Action.
- **By hand:** append an entry to `links.yml`:

```yaml
- url: https://example.com
  title: Example
  note: Why it's useful
  tags: [tag-one, tag-two]
  added: 2026-10-28
  found_via: https://where-i-found-it   # optional
```
