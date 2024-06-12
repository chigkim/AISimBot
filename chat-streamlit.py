import streamlit as st
api_key=st.secrets["OPENAI_API_KEY"]
#model = "gpt-3.5-turbo"
model = "gpt-4o"
from openai import OpenAI
from io import BytesIO
from st_audiorec import st_audiorec
import streamlit.components.v1 as components
import codecs

@st.cache_resource
def get_file(file):
	print(f"Getting {file}")
	return codecs.open(file, "r", "utf-8").read()

@st.cache_resource
def client():
	return OpenAI(api_key=api_key)

@st.cache_resource
def assistant():
	assistants = client().beta.assistants.list()
	for a in assistants:
		if "Patient Sim" in a.name:
			client().beta.assistants.delete(a.id)
	instruction = get_file("instruction.txt")
	return client().beta.assistants.create(name="Patient Sim", instructions=instruction, model=model)

def generate():
	stream = client().beta.threads.runs.create(thread_id=st.session_state.thread.id, assistant_id=assistant().id, stream=True)
	for event in stream:
		try:
			text = event.data.delta.content[0].text.value
			yield text
		except: pass

@st.cache_resource
def transcribe(wav):
	print("Transcribing")
	file = BytesIO(wav)
	file.name="speech.wav"
	try:
		response = client().audio.transcriptions.create(file=file, model="whisper-1", language="en", response_format="text")
		st.session_state.prompt = response
	except Exception as e: st.write(e)

@st.cache_resource
def speak(text):
	try:
		return client().audio.speech.create(model="tts-1", voice="alloy", input=text)
	except: pass

def process(prompt):
	print("Processing ", prompt)
	client().beta.threads.messages.create(thread_id=st.session_state.thread.id, role='user', content=prompt)
	with st.chat_message("user"):
		st.write("user:")
		st.write(prompt)

	with st.chat_message("assistant"):
		st.write("assistant:")
		response = st.write_stream(generate)
	speech = speak(response)
	st.audio(speech.read(), autoplay=True)

def toggle_mic():
	js = get_file("toggle_mic.js").replace("{{state}}", st.session_state.mic_label)
	components.html(js, height=0)

def prepare_audio():
	css = get_file("style.css")
	st.write(css, unsafe_allow_html=True)

	if wav:=st_audiorec():
		if len(wav)>1000:
			transcribe(wav)
		else:
			st.write("Please try again, no sound was recorded.")
			st.session_state.mic_label = "Send"
			toggle_mic()
			st.session_state.mic_label = "Record"

	js = get_file("remove_recorder.js")
	components.html(js, height=0)

@st.cache_resource
def refresh(messages):
	print("Refreshing messages.")
	messages = reversed(messages)
	for m in messages:
		with st.chat_message(m['role']):
			st.write(m['role'])
			st.write(m['content'])

def main():
	if "count" not in st.session_state:
		st.session_state.count = 0
	st.session_state.count += 1
	print(st.session_state.count, "Start:", st.session_state)

	st.title("Paitient Sim")
	prepare_audio()

	if "thread" not in st.session_state:
		st.session_state.thread = client().beta.threads.create()

	messages = [{"role":m.role, "content":m.content[0].text.value} for m in client().beta.threads.messages.list(thread_id=st.session_state.thread.id).data]
	refresh(messages)

	if "prompt" not in st.session_state:
		st.session_state.prompt = None
	if st.session_state.prompt:
		process(st.session_state.prompt)
		st.session_state.prompt = None

	if "mic_label" not in st.session_state:
		st.session_state.mic_label = "Record"
	if st.button(st.session_state.mic_label):
		toggle_mic()
		st.session_state.mic_label = "Record" if st.session_state.mic_label == "Send" else "Send"

	if prompt := st.chat_input("Say Something"):
		st.session_state.prompt = prompt
		st.rerun()

	print(st.session_state.count, "End", st.session_state)

if __name__ == "__main__":
	main()
