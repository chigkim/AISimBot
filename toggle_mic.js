<script>
const state = "{{state}}";

function toggle() {
	const frame = window.parent.document.querySelector("iframe[title*='st_audiorec']");
	const record = frame.contentDocument.querySelector("#record");
	const stop = frame.contentDocument.querySelector("#stop");

	if (frame && record && stop) {
		if (state=="Record") {
			record.click();
		} else {
			stop.click();
		}
	}
}
toggle()
</script>