<script>
	function waitForIframe(selector) {
		const observer = new MutationObserver((mutationsList, observer) => {
			for (let mutation of mutationsList) {
				if (mutation.type === 'childList') {
					const iframe = window.parent.document.querySelector(selector);
					if (iframe) {
						iframe.style.display = "none";
						const reset = frame.contentDocument.querySelector("#reset");
						if (reset) {
							reset.click();
						}
					}
				}
			}
		});
	
		observer.observe(window.parent.document, { childList: true, subtree: true });
	}
	
	document.addEventListener('DOMContentLoaded', () => {
		waitForIframe('iframe[title="st_audiorec.st_audiorec"]');
	});
</script>