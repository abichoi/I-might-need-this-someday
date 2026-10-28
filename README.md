# I-might-need-this-someday
A place for me to store websites where I might find it useful someday

## Browsing and adding links

- **Search page:** https://abichoi.github.io/I-might-need-this-someday/ (served by GitHub Pages from `index.html`)
- **Add a link:** use **+ Add link** on the page. It opens a pre-filled issue; submitting it runs the `Add link from issue` Action, which appends the entry to `links.yml` and closes the issue.
- **By hand:** append an entry to `links.yml`:

```yaml
- url: https://example.com
  title: Example
  note: Why it's useful
  tags: [tag-one, tag-two]
  added: 2026-10-28
  found_via: https://where-i-found-it   # optional
```
