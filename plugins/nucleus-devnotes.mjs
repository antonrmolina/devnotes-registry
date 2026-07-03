import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { join, dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function truncate(str, n) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n).trimEnd() + '…' : str;
}

function licenseBadge(license) {
  const isCern = license && license.startsWith('CERN');
  const bg = isCern ? '#1D9E75' : '#888888';
  const label = isCern ? 'CERN-OHL-P' : 'CC-BY';
  return `<span class="dn-badge" style="background:${bg};color:#fff;">${label}</span>`;
}

function renderCard(entry) {
  const authors = (entry.authors || [])
    .map(a => {
      const aff = a.affiliation
        ? ` &middot; <span class="dn-affil">${a.affiliation}</span>`
        : '';
      return `${a.name}${aff}`;
    })
    .join(', ');

  const pills = (entry.collections || [])
    .map(t => `<span class="dn-pill">${t}</span>`)
    .join(' ');

  // MyST rewrites <img> tags in raw HTML nodes and strips class/style attributes,
  // so sizing is applied via a wrapper div with background-image instead.
  const thumb = entry.thumbnail_url
    ? `<div class="dn-thumb" style="background-image:url('${entry.thumbnail_url}');background-size:cover;background-position:center;"></div>`
    : `<div class="dn-thumb dn-thumb-placeholder"></div>`;

  return `<div class="dn-card">
  ${thumb}
  <div class="dn-body">
    <div class="dn-title">${entry.title}</div>
    <div class="dn-date">${formatDate(entry.date)}</div>
    ${authors ? `<div class="dn-authors">${authors}</div>` : ''}
    <div class="dn-desc">${truncate(entry.description, 120)}</div>
    <div class="dn-meta">
      ${licenseBadge(entry.license)}
      ${pills}
    </div>
    <div class="dn-open"><a href="${entry.devnote_url}" target="_blank" rel="noopener noreferrer">Open DevNote →</a></div>
  </div>
</div>`;
}

const nucleusDevnotesDirective = {
  name: 'nucleus-devnotes',
  run() {
    let entries = [];
    try {
      const indexPath = join(__dirname, '..', 'devnotes-index.json');
      entries = JSON.parse(readFileSync(indexPath, 'utf8'));
    } catch (e) {
      return [{
        type: 'html',
        value: `<p style="color:red">Error loading devnotes-index.json: ${e.message}</p>`
      }];
    }

    entries.sort((a, b) => (b.date > a.date ? 1 : b.date < a.date ? -1 : 0));

    const cards = entries.map(renderCard).join('\n');
    const html = `<div class="dn-grid">\n${cards}\n</div>`;

    return [{ type: 'html', value: html }];
  }
};

export default {
  name: 'nucleus-devnotes',
  directives: [nucleusDevnotesDirective]
};
