// ==========================================================================
// Tool output
// ==========================================================================

class ToolOutput {

	constructor() {
		this._groupSeq = 0;
	}

	// Return direct child matching selector without relying on :scope support.
	_directChild(parent, selector) {
		if (!parent || !parent.children) return null;
		const children = Array.from(parent.children);
		for (let i = 0; i < children.length; i++) {
			const child = children[i];
			try {
				if (child.matches(selector)) return child;
			} catch (_) {}
		}
		return null;
	}

	// Extract raw tool names from a rendered tool-output wrapper.
	_toolNames(outputEl) {
		if (!outputEl) return [];
		const raw = outputEl.getAttribute('data-tool-names') || '';
		if (raw) {
			try {
				const parsed = JSON.parse(raw);
				if (Array.isArray(parsed)) return parsed.map(v => String(v || 'tool'));
			} catch (_) {}
		}
		const nameEl = outputEl.querySelector('.tool-output-name');
		if (!nameEl) return [];
		const text = String(nameEl.textContent || '').trim();
		return text ? [text] : [];
	}

	// Build the compact parent label: "Tools: a, b … and N more".
	_groupSummary(groupEl) {
		if (!groupEl) return;
		const names = [];
		const content = this._directChild(groupEl, '.tool-group-content');
		if (content) {
			const outputs = content.querySelectorAll('.tool-output:not(.tool-output-group)');
			outputs.forEach(el => names.push(...this._toolNames(el)));
		}

		const namesEl = this._directChild(
			this._directChild(groupEl, '.tool-output-toggle.tool-group-toggle'),
			'.tool-output-name.tool-group-names'
		);
		if (!namesEl) return;

		// Parent summary only: show the newest tools first. The expanded
		// group content itself keeps the original chronological order.
		const shown = names.slice().reverse().slice(0, 2);
		let label = shown.join(', ');
		const remaining = Math.max(0, names.length - shown.length);
		if (remaining > 0) {
			const tpl = (typeof window !== 'undefined' && window.LOCALE_TOOL_MORE)
				? String(window.LOCALE_TOOL_MORE)
				: 'and {count} more';
			const more = tpl.split('{count}').join(String(remaining));
			label += `${label ? ' … ' : ''}${more}`;
		}
		namesEl.textContent = label || 'tool';
	}

	// Return metadata for a direct message box that can participate in grouping.
	_groupCandidate(box) {
		if (!box || !box.classList || !box.classList.contains('msg-bot')) return null;

		if (box.classList.contains('tool-group-box')) {
			const msg = this._directChild(box, '.msg');
			const group = this._directChild(msg, '.tool-output-group');
			return (msg && group) ? {box, msg, group} : null;
		}

		const msg = this._directChild(box, '.msg');
		const output = this._directChild(msg, '.tool-output:not(.tool-output-group)');
		if (!msg || !output) return null;

		let toolOnly = box.getAttribute('data-tool-only');
		if (toolOnly == null) {
			// Backward/alternate render-path fallback.  A named tool-output with no
			// markdown response is the same "tool-only" shape used by the template.
			const hasNamedTool = !!output.getAttribute('data-tool-names');
			const hasAssistantText = !!this._directChild(msg, '.md-block');
			toolOnly = (hasNamedTool && !hasAssistantText) ? '1' : '0';
		}
		if (toolOnly !== '1') return null;
		return {box, msg, output, group: null};
	}

	// Create a parent tool group around two consecutive tool-only messages.
	_createGroup(first, second) {
		if (!first || !second || !first.box || !second.box) return first;
		const parent = document.createElement('div');
		parent.className = 'msg-box msg-bot tool-group-box';
		parent.setAttribute('data-tool-only', '1');

		const firstHeader = this._directChild(first.box, '.name-header');
		if (firstHeader) parent.appendChild(firstHeader);

		const msg = document.createElement('div');
		msg.className = 'msg';
		const group = document.createElement('div');
		group.className = 'tool-output tool-output-group';
		const firstId = first.box.id || `runtime-${++this._groupSeq}`;
		const groupId = `tool-group-${firstId}`;
		group.id = groupId;

		const toggle = document.createElement('button');
		toggle.type = 'button';
		toggle.className = 'tool-output-toggle tool-group-toggle';
		toggle.setAttribute('aria-expanded', 'false');
		const expandTitle = (typeof trans !== 'undefined' && trans) ? trans('action.cmd.expand') : 'Expand';
		toggle.setAttribute('title', expandTitle);
		toggle.addEventListener('click', () => this.toggleGroup(groupId));

		const label = document.createElement('span');
		label.className = 'tool-output-label';
		const strong = document.createElement('b');
		strong.textContent = (typeof window !== 'undefined' && window.LOCALE_TOOLS)
			? String(window.LOCALE_TOOLS)
			: 'Tools';
		label.appendChild(strong);
		label.appendChild(document.createTextNode(':\u00a0'));

		const names = document.createElement('span');
		names.className = 'tool-output-name tool-group-names';

		const arrow = document.createElement('img');
		arrow.className = 'tool-output-arrow tool-group-arrow';
		arrow.width = 25;
		arrow.height = 25;
		arrow.alt = '';
		if (typeof window !== 'undefined' && window.ICON_EXPAND) arrow.src = window.ICON_EXPAND;

		toggle.appendChild(label);
		toggle.appendChild(names);
		toggle.appendChild(arrow);

		const content = document.createElement('div');
		content.className = 'tool-group-content';
		content.style.display = 'none';

		group.appendChild(toggle);
		group.appendChild(content);
		msg.appendChild(group);
		parent.appendChild(msg);

		first.box.parentNode.insertBefore(parent, first.box);
		content.appendChild(first.box);
		content.appendChild(second.box);
		this._groupSummary(group);
		return {box: parent, msg, group};
	}

	// Append another consecutive tool-only message to an existing parent group.
	_appendToGroup(groupCandidate, next) {
		if (!groupCandidate || !groupCandidate.group || !next || !next.box) return groupCandidate;
		const content = this._directChild(groupCandidate.group, '.tool-group-content');
		if (!content) return groupCandidate;
		content.appendChild(next.box);
		this._groupSummary(groupCandidate.group);
		return groupCandidate;
	}

	// Group only explicit continuation edges. This runs after both full-history
	// rendering and incremental appends, so behavior stays identical in real time.
	groupConsecutive(root) {
		if (!root || !root.children) return;
		const boxes = Array.from(root.children);
		let anchor = null;

		for (let i = 0; i < boxes.length; i++) {
			const box = boxes[i];
			const candidate = this._groupCandidate(box);
			if (!candidate) {
				anchor = null;
				continue;
			}

			if (!anchor) {
				anchor = candidate;
				continue;
			}

			// An already-built group may absorb the next explicit continuation.
			// A fresh tool message joins the preceding one only when Python marked
			// it as the internal continuation of that exact tool request.
			const isContinuation = box.getAttribute('data-tool-chain-continuation') === '1';
			if (!isContinuation) {
				anchor = candidate;
				continue;
			}

			if (anchor.group) anchor = this._appendToGroup(anchor, candidate);
			else anchor = this._createGroup(anchor, candidate);
		}
	}

	// Toggle a parent tool group. Individual tools remain independently collapsed.
	toggleGroup(id) {
		const groupEl = document.getElementById(String(id || ''));
		if (!groupEl) return;
		const content = this._directChild(groupEl, '.tool-group-content');
		if (!content) return;
		const expanded = content.style.display === 'none';
		content.style.display = expanded ? 'block' : 'none';

		const header = this._directChild(groupEl, '.tool-output-toggle.tool-group-toggle');
		if (header) header.setAttribute('aria-expanded', expanded ? 'true' : 'false');
		const arrow = header ? header.querySelector('.tool-group-arrow') : null;
		if (arrow) arrow.classList.toggle('toggle-expanded', expanded);
	}

	// Placeholder for loader show (can be extended by host).
	showLoader() {
		return;
	}

	// Hide spinner elements in bot messages.
	hideLoader() {
		const elements = document.querySelectorAll('.msg-bot');
		if (elements.length > 0) elements.forEach(el => {
			const s = el.querySelector('.spinner');
			if (s) s.style.display = 'none';
		});
	}

	// Begins a new tool session.
	begin() {
		this.showLoader();
	}

	// Ends the current tool session.
	end() {
		this.hideLoader();
	}

	// Enables the tool output area.
	enable() {
		const els = document.querySelectorAll('.tool-output');
		if (els.length) els[els.length - 1].style.display = 'block';
	}

	// Disables the tool output area.
	disable() {
		const els = document.querySelectorAll('.tool-output');
		if (els.length) els[els.length - 1].style.display = 'none';
	}

	// Append tool output. Structured tool blocks keep the request intact and
	// append only to the Result section; legacy blocks keep the old HTML path.
	append(content) {
		this.hideLoader();
		this.enable();
		const els = document.querySelectorAll('.tool-output');
		if (els.length) {
			const contentEl = els[els.length - 1].querySelector('.content');
			if (!contentEl) return;
			const resultEl = contentEl.querySelector('.tool-output-result-data');
			if (resultEl) {
				resultEl.insertAdjacentText('beforeend', content == null ? '' : String(content));
			} else {
				contentEl.insertAdjacentHTML('beforeend', content == null ? '' : String(content));
			}
		}
	}

	// Replace tool output. Structured tool blocks replace only Result, keeping
	// the Tool request visible after expansion.
	update(content) {
		this.hideLoader();
		this.enable();
		const els = document.querySelectorAll('.tool-output');
		if (els.length) {
			const contentEl = els[els.length - 1].querySelector('.content');
			if (!contentEl) return;
			const resultEl = contentEl.querySelector('.tool-output-result-data');
			if (resultEl) {
				resultEl.textContent = content == null ? '' : String(content);
			} else {
				contentEl.innerHTML = content == null ? '' : String(content);
			}
		}
	}

	// Clear only Result in structured tool blocks; legacy blocks are cleared
	// exactly as before.
	clear() {
		this.hideLoader();
		this.enable();
		const els = document.querySelectorAll('.tool-output');
		if (els.length) {
			const contentEl = els[els.length - 1].querySelector('.content');
			if (!contentEl) return;
			const resultEl = contentEl.querySelector('.tool-output-result-data');
			if (resultEl) resultEl.replaceChildren();
			else contentEl.replaceChildren();
		}
	}
	
	// Toggle visibility of a specific tool output block by message id.
	toggle(id) {
		let outputEl = document.getElementById('tool-output-' + id);
		if (!outputEl) {
			const el = document.getElementById('msg-bot-' + id);
			if (!el) return;
			outputEl = el.querySelector('.tool-output:not(.tool-output-group)');
		}
		if (!outputEl) return;
		const contentEl = outputEl.querySelector('.content');
		if (!contentEl) return;

		const expanded = contentEl.style.display === 'none';
		contentEl.style.display = expanded ? 'block' : 'none';

		const headerEl = outputEl.querySelector('.tool-output-toggle');
		if (headerEl) headerEl.setAttribute('aria-expanded', expanded ? 'true' : 'false');

		const arrowEl = outputEl.querySelector('.tool-output-arrow') || outputEl.querySelector('.toggle-cmd-output img');
		if (arrowEl) arrowEl.classList.toggle('toggle-expanded', expanded);
	}
}