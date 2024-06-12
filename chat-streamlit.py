import streamlit as st
#api_key=st.secrets["OPENAI_API_KEY"]
#model = "gpt-3.5-turbo"
model = "gpt-4o"
from openai import OpenAI
from io import BytesIO
from st_audiorec import st_audiorec
import streamlit.components.v1 as components
import codecs

@st.cache_resource
def client():
	return OpenAI(api_key=api_key)

@st.cache_resource
def assistant():
	assistants = client().beta.assistants.list()
	for a in assistants:
		if "Patient Sim" in a.name:
			client().beta.assistants.delete(a.id)
	instruction = codecs.open("instruction.txt", "r", "utf-8").read()
	return client().beta.assistants.create(name="Patient Sim", instructions=instruction, model=model)

def generate():
	stream = client().beta.threads.runs.create(thread_id=st.session_state.thread.id, assistant_id=assistant().id, stream=True)
	for event in stream:
		try:
			text = event.data.delta.content[0].text.value
			yield text
		except: pass

def transcribe(wav):
	file = BytesIO(wav)
	file.name="speech.wav"
	response = client().audio.transcriptions.create(
		file=file,
		model="whisper-1",
		language="en",
		response_format="text"
	)
	st.session_state.prompt = response

@st.cache_resource
def speak(text):
	return client().audio.speech.create(model="tts-1", voice="alloy", input=text)

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
	js = open("toggle_mic.js").read()
	js = js.replace("{{state}}", st.session_state.mic_label)
	components.html(js, height=0)

def prepare_audio():
	style = open("style.css").read()
	st.write(style, unsafe_allow_html=True)

	if wav:=st_audiorec():
		transcribe(wav)
	js = open("remove_recorder.js").read()
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
