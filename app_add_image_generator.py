# ✅ Gradio 기반 디자인 피드백 앱 - 채팅 기반 개선 이미지 생성 추가
import gradio as gr
from PIL import Image
from io import BytesIO
import base64
import datetime
import openai
import os
import requests

# === 1. base64 인코딩 ===
def encode_image_to_base64(pil_image):
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# === 2. 모델 목록 받아오기 함수 ===
def get_openai_model_list(api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list()
        model_ids = [m.id for m in models.data if any(m.id.startswith(p) for p in ["gpt-4", "gpt-3.5"])]
        return sorted(model_ids)
    except Exception as e:
        return [f"❌ 모델 목록 불러오기 실패: {e}"]

# === 3. GPT 호출 함수 ===
def generate_response_openai(image: Image.Image, prompt: str, chat_history, api_key: str, system_prompt: str, model_name: str):
    if not api_key:
        return "❌ API 키를 입력해주세요.", None
    client = openai.OpenAI(api_key=api_key)
    base64_image = encode_image_to_base64(image)

    context_pairs = []
    if chat_history:
        for i in range(0, len(chat_history)-1, 2):
            if i+1 < len(chat_history):
                user_msg = chat_history[i][1]
                ai_msg = chat_history[i+1][1]
                context_pairs.append(f"사용자: {user_msg}\nAI: {ai_msg}")
    context = "\n".join(context_pairs)

    system_msg = {"role": "system", "content": system_prompt}
    user_msg = {
        "role": "user",
        "content": [
            {"type": "text", "text": f"{context}\n사용자: {prompt}"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    }

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[system_msg, user_msg],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return f"❌ OpenAI API 오류: {str(e)}", None


# === 4. 개선 이미지 + 선택 버튼 HTML 생성 ===
def generate_modal_images_html(image_urls):
    modal_blocks = []
    for i, url in enumerate(image_urls):
        modal_blocks.append(f'''
        <div style="display:inline-block;text-align:center;margin:8px;">
            <img class="modal-img" src="{url}" onclick="document.getElementById('modal-{i}').style.display='block'">
            <div id="modal-{i}" class="modal-overlay" onclick="this.style.display='none'">
                <img src="{url}" />
            </div>
        </div>
        ''')
    modal_css = '''
    <style>
    .modal-img {
        max-height: 200px;
        cursor: pointer;
        transition: 0.3s;
        border-radius: 8px;
        border: 1px solid #ccc;
        margin-right: 8px;
    }
    .modal-overlay {
        display: none;
        position: fixed;
        z-index: 999;
        left: 0;
        top: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(0,0,0,0.7);
    }
    .modal-overlay img {
        display: block;
        max-width: 90vw;
        max-height: 90vh;
        margin: 5vh auto;
        border-radius: 10px;
    }
    </style>
    '''
    return modal_css + ''.join(modal_blocks)

# === 4. 채팅 기반 UI 개선 이미지 생성 ===
def apply_chat_feedback_to_image(chat_history, image, api_key, dalle_model):
    if not api_key or not image:
        return chat_history, "<div class='bubble ai-bubble'>❌ API 키와 이미지가 필요합니다.</div>"

    feedback_prompt = "This is a conversation between a user and a design assistant.\n"
    for role, msg in chat_history:
        feedback_prompt += f"{role}: {msg}\n"
    feedback_prompt += "\nPlease redesign the UI based on this discussion."

    client = openai.OpenAI(api_key=api_key)
    image_urls = []
    try:
        for _ in range(3):  # ✅ DALL·E 3을 세 번 호출해서 3장 생성
            result = client.images.generate(
                model=dalle_model,
                prompt=feedback_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_urls.append(result.data[0].url)

        modal_html = generate_modal_images_html(image_urls)
        chat_history.append(("AI", "아래는 개선된 UI 디자인 예시들입니다."))
        chat_history.append(("AI", modal_html))
        return chat_history,modal_html, image_urls
    except Exception as e:
        chat_history.append(("AI", f"❌ 이미지 생성 실패: {e}"))
        return chat_history, "", []

# === 5. 기본 채팅 처리 ===
def chat_with_model(chat_history, image, user_message, api_key, system_prompt, model_name):
    if not user_message.strip():
        return chat_history, "", ""
    chat_history.append(("사용자", user_message))
    if not image:
        chat_history.append(("AI", "❌ 이미지를 반드시 업로드해주세요."))
        return chat_history, "", ""
    bot_response, _ = generate_response_openai(image, user_message, chat_history, api_key, system_prompt, model_name)
    chat_history.append(("AI", bot_response))
    return chat_history, "", ""

# === 6. Gradio UI 구성 ===
with gr.Blocks(
    css="""
    /* 전체 컨테이너 스타일 */
    .container {
        width: 100%;
        margin: 0 auto;
    }
    
    /* 이미지 업로드 영역 */
    .image-upload-container {
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    /* 이미지 업로드 컴포넌트 크기 조정 */
    .image-upload-container > div {
        height: 100%;
    }
    
    /* 이미지 컨테이너를 더 크게 */
    .image-upload-container .upload-container {
        min-height: 600px;
    }
    
    /* 업로드된 이미지가 더 크게 보이도록 */
    .image-upload-container img {
        max-height: 550px !important;
        object-fit: contain;
    }
    
    /* 채팅 컨테이너 */
    .chat-container {
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    /* 말풍선 스타일 */
    .chatbox {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 10px;
        height: 600px;  /* 높이 증가 */
        overflow-y: auto;
        background-color: #f5f5f5;
        border-radius: 10px;
    }
    
    .message {
        display: flex;
        max-width: 80%;
    }
    
    .user-msg {
        align-self: flex-end;
        justify-content: flex-end;
        margin-left: auto;
    }
    
    .ai-msg {
        align-self: flex-start;
        margin-right: auto;
    }
    
    .bubble {
        padding: 10px 15px;
        border-radius: 18px;
        line-height: 1.4;
        font-size: 15px;
        word-break: break-word;
    }
    
    .user-bubble {
        background-color: #FEE500; /* 카카오톡 노란색 */
        border-bottom-right-radius: 0;
    }
    
    .ai-bubble {
        background-color: white;
        border-bottom-left-radius: 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* 입력 영역 스타일 */
    .input-area {
        display: flex;
        gap: 8px;
        margin-top: 10px;
    }
    
    /* 시간 표시 */
    .time {
        font-size: 12px;
        color: #999;
        margin-top: 2px;
        text-align: right;
    }
    
    /* 사용자 이름 */
    .sender {
        font-size: 12px;
        color: #666;
        margin-bottom: 2px;
    }
    
    /* 프로필 이미지 */
    .profile {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        margin-right: 8px;
        background-color: #ddd;
        flex-shrink: 0;
    }
    
    /* 대화 기록 표시 */
    .history-indicator {
        text-align: center;
        margin: 10px 0;
        font-size: 12px;
        color: #888;
        font-style: italic;
    }
    
    /* 초기화 버튼 스타일 */
    .reset-button {
        margin-top: 10px;
        text-align: center;
    }

    /* 모델 정보 표시 */
    .model-info {
        margin-top: 15px;
        padding: 8px;
        background-color: #f0f0f0;
        border-radius: 5px;
        font-size: 13px;
        color: #555;
    }
""") as demo:
    gr.Markdown("## 💬 디자인 피드백 웹 앱 Demo (OpenAI 모델 기반)")

    api_key_input = gr.Textbox(label="🔑 OpenAI API 키 입력", placeholder="sk-...", type="password")
    api_key_state = gr.State("")
    system_prompt_input = gr.Textbox(label="🛠️ System Prompt 입력 (선택)", placeholder="You are a UX/UI design expert...", value="You are a helpful design assistant.")
    system_prompt_state = gr.State("You are a helpful design assistant.")
    model_dropdown = gr.Dropdown(label="🤖 사용할 모델 선택", choices=["(API 키 먼저 입력하세요)"])
    model_state = gr.State("gpt-4o")

    with gr.Row(equal_height=True):
        with gr.Column(scale=4):
            image_input = gr.Image(type="pil", label="디자인 이미지 업로드 (필수)", interactive=True, height=650)
            with gr.Row():
                reset_btn = gr.Button("대화 초기화", variant="secondary")

        with gr.Column(scale=3):
            chat_state = gr.State([])
            selected_image_url = gr.State("")
            improved_image_urls = gr.State([])
            chatbox = gr.HTML(value="<div class='chatbox'><div class='history-indicator'>이전 대화 기록이 모델에 전달됩니다</div></div>", elem_id="chatbox")
            with gr.Row():
                user_input = gr.Textbox(placeholder="질문을 입력하세요...", show_label=False)
                submit_btn = gr.Button("전송", variant="primary")
                apply_btn = gr.Button("🛠️ 개선 사항 적용", variant="secondary")
                select_buttons = [gr.Button(f"✅ {i+1}번 이미지 선택") for i in range(3)]
                apply_selected_btn = gr.Button("✅ 선택한 이미지 적용", variant="primary")

    def get_current_time():
        now = datetime.datetime.now()
        return now.strftime("%p %I:%M").lower()

    def reset_chat():
        return [], "<div class='chatbox'><div class='history-indicator'>이전 대화 기록이 모델에 전달됩니다</div></div>", ""

    def render_chat(chat_history):
        messages_html = "<div class='history-indicator'>이전 대화 기록이 모델에 전달됩니다</div>"
        current_time = get_current_time()
        for role, msg in chat_history:
            if role == "사용자":
                messages_html += f"<div class='message user-msg'><div><div class='bubble user-bubble'>{msg}</div><div class='time'>{current_time}</div></div></div>"
            else:
                messages_html += f"<div class='message ai-msg'><div class='profile'></div><div><div class='sender'>AI 도우미</div><div class='bubble ai-bubble'>{msg}</div><div class='time'>{current_time}</div></div></div>"
        return f"<div class='chatbox'>{messages_html}</div>"

    def submit_message(chat_state, image, message, api_key, system_prompt, model_name):
        if not message.strip():
            return chat_state, render_chat(chat_state), ""
        new_history, _, _ = chat_with_model(chat_state, image, message, api_key, system_prompt, model_name)
        return new_history, render_chat(new_history), ""
    
    def select_image(url, index):
        return url[index]

    def apply_selected_image(selected_url):
        if selected_url:
            img_data = requests.get(selected_url).content
            img = Image.open(BytesIO(img_data))
            return img
        else:
            print("empty\n")
            return None

    def apply_button_action(chat_state, image, api_key, dalle_model):
        new_history, modal_html, image_urls = apply_chat_feedback_to_image(chat_state, image, api_key, dalle_model)
        return new_history, render_chat(new_history), image_urls

    def update_models(api_key):
        models = get_openai_model_list(api_key)
        default = "gpt-4o" if "gpt-4o" in models else models[0]
        return gr.update(choices=models, value=default), default

    api_key_input.change(lambda k: k, inputs=api_key_input, outputs=api_key_state)
    api_key_input.change(fn=update_models, inputs=api_key_input, outputs=[model_dropdown, model_state])
    model_dropdown.change(lambda m: m, inputs=model_dropdown, outputs=model_state)
    system_prompt_input.change(lambda p: p, inputs=system_prompt_input, outputs=system_prompt_state)

    submit_btn.click(fn=submit_message, inputs=[chat_state, image_input, user_input, api_key_state, system_prompt_state, model_state], outputs=[chat_state, chatbox, user_input])
    user_input.submit(fn=submit_message, inputs=[chat_state, image_input, user_input, api_key_state, system_prompt_state, model_state], outputs=[chat_state, chatbox, user_input])

    apply_btn.click(fn=apply_button_action, inputs=[chat_state, image_input, api_key_state, gr.State("dall-e-3")], outputs=[chat_state, chatbox, improved_image_urls])
    reset_btn.click(fn=reset_chat, inputs=[], outputs=[chat_state, chatbox, user_input])

    select_buttons[0].click(fn=lambda urls: urls[0], inputs=[improved_image_urls], outputs=[selected_image_url])
    select_buttons[1].click(fn=lambda urls: urls[1], inputs=[improved_image_urls], outputs=[selected_image_url])
    select_buttons[2].click(fn=lambda urls: urls[2], inputs=[improved_image_urls], outputs=[selected_image_url])

    apply_selected_btn.click(
        fn=apply_selected_image,
        inputs=[selected_image_url],
        outputs=[image_input]
    )

if __name__ == "__main__":
    print("웹 앱 실행 중...", flush=True)
    demo.launch(share=True)