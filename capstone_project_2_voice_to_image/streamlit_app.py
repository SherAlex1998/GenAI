import hashlib
import streamlit as st
from audio_recorder_streamlit import audio_recorder

from services.image_service import ImageGenerationService
from services.llm_agent import LLMAgent
from services.logger import get_logs, log
from services.stt_service import ModelDownloadError, VoskSTTService


@st.cache_resource
def get_stt_service() -> VoskSTTService:
    log("Initializing STT service instance.")
    return VoskSTTService()


@st.cache_resource
def get_llm_agent() -> LLMAgent:
    log("Initializing LLM agent instance.")
    return LLMAgent()


@st.cache_resource
def get_image_service() -> ImageGenerationService:
    log("Initializing image generation service instance.")
    return ImageGenerationService()


def render_sidebar() -> None:
    st.sidebar.header("Logs")
    
    logs = get_logs()
    
    if "last_log_count" not in st.session_state:
        st.session_state.last_log_count = len(logs)
    
    current_log_count = len(logs)
    
    if current_log_count > st.session_state.last_log_count:
        st.session_state.last_log_count = current_log_count
    
    if logs:
        st.sidebar.code("\n".join(logs[-200:]), language="text")
    else:
        st.sidebar.info("No entries yet.")


def main() -> None:
    st.set_page_config(page_title="Speech Recognition", page_icon="🗣️")
    render_sidebar()

    st.title("Speech Recognition (Vosk)")
    st.write(
        "Record a short voice message in English. "
        "When you finish, the recording will be processed automatically."
    )

    size_labels = {
        "1024x1024": "1024x1024",
        "1024x1536": "1024x1536",
        "1536x1024": "1536x1024",
    }
    selected_size_label = st.selectbox(
        "Generated image size",
        options=list(size_labels.keys()),
        format_func=lambda key: size_labels[key],
    )
    log(f"Image size selected: {selected_size_label}")
    stt_service = None
    llm_agent = None
    try:
        stt_service = get_stt_service()
    except ModelDownloadError as exc:
        st.error(
            "Failed to prepare the Vosk model. Check your internet connection and restart the app."
        )
        log(f"[Error] STT initialization failed: {exc}")
        st.stop()
        return

    try:
        llm_agent = get_llm_agent()
    except Exception as exc:
        st.error("Failed to initialize the LLM agent. Verify your API settings.")
        log(f"[Error] LLM agent initialization failed: {exc}")
        st.stop()
        return

    try:
        image_service = get_image_service()
    except Exception as exc:
        st.error("Failed to initialize the image generation service.")
        log(f"[Error] Image service initialization failed: {exc}")
        st.stop()
        return

    audio_bytes = audio_recorder(
        text="Click to start recording", recording_color="#e74c3c", neutral_color="#6c757d"
    )

    if audio_bytes:
        audio_hash = hashlib.md5(audio_bytes).hexdigest()
        
        if "processed_audio" not in st.session_state:
            st.session_state.processed_audio = None
        if "last_transcript" not in st.session_state:
            st.session_state.last_transcript = None
        if "last_prompt" not in st.session_state:
            st.session_state.last_prompt = None
        if "last_image_payload" not in st.session_state:
            st.session_state.last_image_payload = None
        
        is_new_audio = st.session_state.processed_audio != audio_hash
        
        if is_new_audio:
            st.audio(audio_bytes, format="audio/wav")
            log("Starting transcription from Streamlit recorder.")
            transcript = None
            prompt = None
            image_payload = None
            
            success_container = st.empty()
            transcript_container = st.empty()

            with st.spinner("Transcribing audio..."):
                try:
                    transcript = stt_service.transcribe(audio_bytes)
                except ValueError as exc:
                    log(f"[Error] Audio validation failed: {exc}")
                    st.error(f"Audio validation error: {exc}")
                except Exception as exc:  # pragma: no cover
                    log(f"[Error] Transcription failed: {exc}")
                    st.error(f"Transcription failed: {exc}")
                else:
                    success_container.success("Done! Recognized text:")
                    transcript_container.write(transcript)
                    log("Transcript delivered to UI.")

            if transcript and transcript.strip() and transcript != "(no transcription output)":
                with st.spinner("Generating prompt..."):
                    try:
                        prompt = llm_agent.build_image_prompt(transcript)
                    except Exception as exc:
                        log(f"[Error] Prompt generation failed: {exc}")
                        st.error(f"Failed to prepare the prompt: {exc}")
                    else:
                        st.info("Prompt for image generation:")
                        st.code(prompt, language="text")
                        log("Prompt delivered to UI.")
            elif transcript == "(no transcription output)":
                st.warning("No transcription result returned; image generation skipped.")
                log("Transcription empty, skipping prompt and image generation.")

            if prompt and image_service:
                with st.spinner("Generating image..."):
                    try:
                        image_payload = image_service.generate_image(
                            prompt, size=selected_size_label
                        )
                    except Exception as exc:
                        log(f"[Error] Image generation failed: {exc}")
                        st.error(f"Failed to generate the image: {exc}")
                    else:
                        success_container.empty()
                        transcript_container.empty()
                        st.image(image_payload["bytes"], caption="Generated image", use_container_width=True)
                        st.download_button(
                            label="📥 Download image",
                            data=image_payload["bytes"],
                            file_name="generated_image.png",
                            mime="image/png",
                            use_container_width=True
                        )
                        log("Image delivered to UI.")
            
            st.session_state.processed_audio = audio_hash
            st.session_state.last_transcript = transcript
            st.session_state.last_prompt = prompt
            st.session_state.last_image_payload = image_payload
        else:
            st.audio(audio_bytes, format="audio/wav")
            
            if st.session_state.last_transcript:
                st.success("Done! Recognized text:")
                st.write(st.session_state.last_transcript)
            
            if st.session_state.last_prompt:
                st.info("Prompt for image generation:")
                st.code(st.session_state.last_prompt, language="text")
            
            if st.session_state.last_image_payload:
                st.image(
                    st.session_state.last_image_payload["bytes"],
                    caption="Generated image",
                    use_container_width=True
                )
                st.download_button(
                    label="📥 Download image",
                    data=st.session_state.last_image_payload["bytes"],
                    file_name="generated_image.png",
                    mime="image/png",
                    use_container_width=True
                )


if __name__ == "__main__":
    main()

