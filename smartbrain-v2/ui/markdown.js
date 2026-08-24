/**
 * Markdown to HTML renderer with GFM table support.
 * Handles: headers, bold, italic, code blocks (with language),
 * inline code, links, bullets, ordered lists, nested lists, blockquotes,
 * pipe tables (GFM), task lists, horizontal rules, auto-links, strikethrough.
 */
const MarkdownRenderer = (() => {
    function escapeHtml(text) {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return text.replace(/[&<>"']/g, c => map[c]);
    }

    // Render inline-level markdown (bold, italic, code, links, etc.)
    // Protects inline code from being mangled by other regex passes.
    function renderInline(text) {
        const codeSpans = [];
        text = text.replace(/`([^`]+)`/g, (m, code) => {
            codeSpans.push(`<code>${escapeHtml(code)}</code>`);
            return `\x00${codeSpans.length - 1}\x00`;
        });

        // Bold + italic
        text = text.replace(/\*\*\*([^\*]+)\*\*\*/g, '<strong><em>$1</em></strong>');
        // Bold
        text = text.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/__([^_]+)__/g, '<strong>$1</strong>');
        // Italic
        text = text.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, '$1<em>$2</em>');
        text = text.replace(/(^|[^_])_([^_]+)_(?!_)/g, '$1<em>$2</em>');
        // Strikethrough
        text = text.replace(/~~([^~]+)~~/g, '<del>$1</del>');
        // Explicit links [text](url)
        text = text.replace(
            /\[([^\]]+)\]\(([^)]+)\)/g,
            '<a href="$2" target="_blank" rel="noopener">$1</a>'
        );
        // Auto-link bare URLs (not already inside an anchor)
        text = text.replace(
            /(?<![">])(https?:\/\/[^\s<]+)/g,
            '<a href="$1" target="_blank" rel="noopener">$1</a>'
        );

        // Restore inline code spans
        text = text.replace(/\x00(\d+)\x00/g, (m, idx) => codeSpans[Number(idx)]);
        return text;
    }

    // GFM pipe-table detector: header row, separator row, body rows.
    // Returns { html, consumed } if a table starts at `startIdx`, else null.
    function tryParseTable(lines, startIdx) {
        const headerLine = lines[startIdx];
        const separatorLine = lines[startIdx + 1];
        if (!headerLine || !separatorLine) return null;
        if (!/\|/.test(headerLine)) return null;
        if (!/^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(separatorLine)) return null;

        const splitRow = (line) => {
            const trimmed = line.trim().replace(/^\|/, '').replace(/\|$/, '');
            return trimmed.split(/\s*\|\s*/).map(cell => cell.trim());
        };

        const headers = splitRow(headerLine);
        const aligns = splitRow(separatorLine).map(sep => {
            const left = sep.startsWith(':');
            const right = sep.endsWith(':');
            if (left && right) return 'center';
            if (right) return 'right';
            if (left) return 'left';
            return '';
        });

        const bodyRows = [];
        let i = startIdx + 2;
        while (i < lines.length && /\|/.test(lines[i]) && lines[i].trim() !== '') {
            bodyRows.push(splitRow(lines[i]));
            i++;
        }

        const alignAttr = idx => aligns[idx] ? ` style="text-align:${aligns[idx]}"` : '';
        let html = '<div class="md-table-wrap"><table class="md-table">';
        html += '<thead><tr>';
        headers.forEach((h, idx) => {
            html += `<th${alignAttr(idx)}>${renderInline(h)}</th>`;
        });
        html += '</tr></thead><tbody>';
        bodyRows.forEach(row => {
            html += '<tr>';
            row.forEach((cell, idx) => {
                html += `<td${alignAttr(idx)}>${renderInline(cell)}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table></div>';

        return { html, consumed: i - startIdx };
    }

    function render(markdown) {
        if (!markdown) return '';

        // Normalise line endings + soft-trim trailing whitespace
        const lines = markdown.replace(/\r\n/g, '\n').split('\n');
        const output = [];
        let inCodeBlock = false;
        let codeContent = [];
        let codeLang = '';
        let listStack = []; // [{type: 'ul'|'ol', indent: number}]
        let inBlockquote = false;
        let blockquoteContent = [];
        let paragraphBuffer = [];

        const closeLists = (toDepth = 0) => {
            while (listStack.length > toDepth) {
                const l = listStack.pop();
                output.push(l.type === 'ul' ? '</ul>' : '</ol>');
            }
        };

        const closeBlockquote = () => {
            if (inBlockquote) {
                output.push('<blockquote>' + renderInline(blockquoteContent.join(' ')) + '</blockquote>');
                inBlockquote = false;
                blockquoteContent = [];
            }
        };

        const flushParagraph = () => {
            if (paragraphBuffer.length) {
                output.push('<p>' + renderInline(paragraphBuffer.join(' ')) + '</p>');
                paragraphBuffer = [];
            }
        };

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            // Fenced code blocks
            if (line.startsWith('```')) {
                if (inCodeBlock) {
                    const langClass = codeLang ? ` class="language-${escapeHtml(codeLang)}"` : '';
                    output.push(`<pre><code${langClass}>${escapeHtml(codeContent.join('\n'))}</code></pre>`);
                    inCodeBlock = false;
                    codeContent = [];
                    codeLang = '';
                } else {
                    flushParagraph();
                    closeLists();
                    closeBlockquote();
                    inCodeBlock = true;
                    codeLang = line.slice(3).trim();
                }
                continue;
            }
            if (inCodeBlock) {
                codeContent.push(line);
                continue;
            }

            // Blockquote
            if (line.startsWith('> ')) {
                flushParagraph();
                closeLists();
                if (!inBlockquote) inBlockquote = true;
                blockquoteContent.push(line.slice(2));
                continue;
            } else {
                closeBlockquote();
            }

            // Try table
            const tableResult = tryParseTable(lines, i);
            if (tableResult) {
                flushParagraph();
                closeLists();
                output.push(tableResult.html);
                i += tableResult.consumed - 1;
                continue;
            }

            // Headers
            const headerMatch = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/);
            if (headerMatch) {
                flushParagraph();
                closeLists();
                const level = headerMatch[1].length;
                const text = renderInline(headerMatch[2]);
                output.push(`<h${level}>${text}</h${level}>`);
                continue;
            }

            // Horizontal rule
            if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line) && line.trim().length > 0) {
                flushParagraph();
                closeLists();
                output.push('<hr>');
                continue;
            }

            // Unordered list (with optional nesting via leading spaces)
            const ulMatch = line.match(/^(\s*)[*\-+]\s+(.+)/);
            const olMatch = line.match(/^(\s*)(\d+)\.\s+(.+)/);
            if (ulMatch || olMatch) {
                flushParagraph();
                const indent = (ulMatch ? ulMatch[1] : olMatch[1]).length;
                const type = ulMatch ? 'ul' : 'ol';
                const content = ulMatch ? ulMatch[2] : olMatch[3];

                // Close any deeper/mismatched lists
                while (
                    listStack.length > 0 &&
                    (listStack[listStack.length - 1].indent > indent ||
                        (listStack[listStack.length - 1].indent === indent &&
                            listStack[listStack.length - 1].type !== type))
                ) {
                    const l = listStack.pop();
                    output.push(l.type === 'ul' ? '</ul>' : '</ol>');
                }
                if (
                    listStack.length === 0 ||
                    listStack[listStack.length - 1].indent < indent
                ) {
                    output.push(type === 'ul' ? '<ul>' : '<ol>');
                    listStack.push({ type, indent });
                }

                // Task list checkboxes
                let liText = content;
                const taskMatch = liText.match(/^\[( |x|X)\]\s+(.*)$/);
                if (taskMatch) {
                    const checked = taskMatch[1].toLowerCase() === 'x' ? ' checked' : '';
                    liText = `<input type="checkbox" disabled${checked}> ${taskMatch[2]}`;
                    output.push('<li class="task-item">' + renderInline(liText) + '</li>');
                } else {
                    output.push('<li>' + renderInline(liText) + '</li>');
                }
                continue;
            }

            // Blank line -> paragraph break
            if (line.trim() === '') {
                flushParagraph();
                closeLists();
                continue;
            }

            // Regular paragraph — buffer so consecutive lines merge into one <p>
            closeLists();
            paragraphBuffer.push(line);
        }

        // Close any open blocks
        if (inCodeBlock) {
            const langClass = codeLang ? ` class="language-${escapeHtml(codeLang)}"` : '';
            output.push(`<pre><code${langClass}>${escapeHtml(codeContent.join('\n'))}</code></pre>`);
        }
        flushParagraph();
        closeLists();
        closeBlockquote();

        return output.join('\n');
    }

    return { render, escapeHtml, renderInline };
})();
