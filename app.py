import gradio as gr
from PIL import Image
from io import BytesIO
import base64
import datetime
import openai

# === 1. base64 인코딩 ===
def encode_image_to_base64(pil_image):
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# === 2. OpenRouter 모델 목록 받아오기 함수 ===
def get_openrouter_model_list(api_key):
    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        models = client.models.list()
        # Vision 모델만 필터링 (이미지 처리 가능한 모델들)
        vision_models = []
        for model in models.data:
            model_id = model.id
            # 주요 Vision 모델들 필터링
            if any(keyword in model_id.lower() for keyword in [
                "gpt-4", "claude", "gemini", "llava", "vision", "multimodal"
            ]):
                vision_models.append(model_id)
        
        return sorted(vision_models) if vision_models else [m.id for m in models.data[:20]]
    except Exception as e:
        return [f"❌ 모델 목록 불러오기 실패: {e}"]

# === 3. OpenRouter API 호출 ===
def generate_response_openrouter(image: Image.Image, prompt: str, chat_history, api_key: str, system_prompt: str, model_name: str):
    if not api_key:
        return "❌ API 키를 입력해주세요."
    
    # OpenRouter 클라이언트 설정
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    
    base64_image = encode_image_to_base64(image)

    # 대화 이력 구성
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
            max_tokens=1000,
            # OpenRouter 추가 헤더 (선택사항)
            extra_headers={
                "HTTP-Referer": "http://localhost:7860",  # Gradio 기본 포트
                "X-Title": "Design Feedback Chatbot"
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ OpenRouter API 오류: {str(e)}"

# === 4. 채팅 처리 ===
def chat_with_model(chat_history, image, user_message, api_key, system_prompt, model_name):
    if not user_message.strip():
        return chat_history, ""

    chat_history.append(("사용자", user_message))

    if not image:
        chat_history.append(("AI", "❌ 이미지를 반드시 업로드해주세요."))
        return chat_history, ""
    
    bot_response = generate_response_openrouter(image, user_message, chat_history, api_key, system_prompt, model_name)
    chat_history.append(("AI", bot_response))
    return chat_history, ""

# === 5. UI 구성 ===
with gr.Blocks(css="""
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
    
    /* API 정보 스타일 */
    .api-info {
        margin-bottom: 15px;
        padding: 10px;
        background-color: #e6f3ff;
        border-radius: 8px;
        border-left: 4px solid #0066cc;
    }
""") as demo:
    gr.Markdown("## 💬 디자인 피드백 웹 앱 Demo (OpenRouter 기반)")
    
    # OpenRouter 사용 안내
    with gr.Row():
        gr.HTML("""
        <div class='api-info'>
            <strong>🔑 OpenRouter API 키 발급 방법:</strong><br>
            1. <a href="https://openrouter.ai" target="_blank">OpenRouter.ai</a>에서 계정 생성<br>
            2. API Keys 메뉴에서 새 키 생성<br>
            3. 아래에 발급받은 키를 입력하세요
        </div>
        """)

    api_key_input = gr.Textbox(
        label="🔑 OpenRouter API 키 입력", 
        placeholder="sk-or-v1-...", 
        type="password",
        info="OpenRouter에서 발급받은 API 키를 입력하세요"
    )
    api_key_state = gr.State("")

    # System Prompt 입력
    system_prompt_input = gr.Textbox(
        label="🛠️ System Prompt 입력 (선택)", 
        placeholder="ex: You are a UX/UI design expert...", 
        value="You are a helpful design assistant that provides detailed feedback on UI/UX designs."
    )
    system_prompt_state = gr.State("You are a helpful design assistant that provides detailed feedback on UI/UX designs.")

    # 🔹 모델 드롭다운 추가
    model_dropdown = gr.Dropdown(
        label="🤖 사용할 모델 선택", 
        choices=["(API 키 먼저 입력하세요)"],
        info="Vision 기능을 지원하는 모델들이 우선 표시됩니다"
    )
    model_state = gr.State("openai/gpt-4o")

    # 좌우 분할 레이아웃
    with gr.Row(equal_height=True):
        # 왼쪽 - 이미지 업로드 영역 (더 큰 사이즈로)
        with gr.Column(scale=4, elem_classes="image-upload-container"):
            image_input = gr.Image(
                type="pil", 
                label="디자인 이미지 업로드 (필수)", 
                interactive=True,
                height=650,  # 높이 증가
                elem_classes="upload-container"
            )
            
            # 대화 초기화 버튼 추가
            with gr.Row(elem_classes="reset-button"):
                reset_btn = gr.Button("대화 초기화", variant="secondary")
        
        # 오른쪽 - 채팅 영역
        with gr.Column(scale=3, elem_classes="chat-container"):
            chat_state = gr.State([])
            
            # 채팅 메시지를 보여주는 HTML 컴포넌트
            chatbox = gr.HTML(
                value="<div class='chatbox'><div class='history-indicator'>이전 대화 기록이 모델에 전달됩니다</div></div>",
                elem_id="chatbox"
            )
            
            with gr.Row(elem_classes="input-area"):
                user_input = gr.Textbox(
                    placeholder="질문을 입력하세요...", 
                    show_label=False,
                    elem_id="msg-input"
                )
                submit_btn = gr.Button("전송", variant="primary")

    # === 기능 함수 ===
    def get_current_time():
        now = datetime.datetime.now()
        return now.strftime("%p %I:%M").lower()

    def reset_chat():
        return [], "<div class='chatbox'><div class='history-indicator'>이전 대화 기록이 모델에 전달됩니다</div></div>"

    def render_chat(chat_history):
        messages_html = "<div class='history-indicator'>이전 대화 기록이 모델에 전달됩니다</div>"
        current_time = get_current_time()
        for i, (role, msg) in enumerate(chat_history):
            if role == "사용자":
                messages_html += f"""
                <div class='message user-msg'>
                    <div>
                        <div class='bubble user-bubble'>{msg}</div>
                        <div class='time'>{current_time}</div>
                    </div>
                </div>"""
            else:
                messages_html += f"""
                <div class='message ai-msg'>
                    <div class='profile'></div>
                    <div>
                        <div class='sender'>AI 도우미</div>
                        <div class='bubble ai-bubble'>{msg}</div>
                        <div class='time'>{current_time}</div>
                    </div>
                </div>"""
        return f"<div class='chatbox'>{messages_html}</div>"

    def submit_message(chat_state, image, message, api_key, system_prompt, model_name):
        if not message.strip():
            return chat_state, render_chat(chat_state), ""
        new_history, _ = chat_with_model(chat_state, image, message, api_key, system_prompt, model_name)
        return new_history, render_chat(new_history), ""

    def update_models(api_key):
        if not api_key:
            return gr.update(choices=["(API 키 먼저 입력하세요)"], value="(API 키 먼저 입력하세요)"), "(API 키 먼저 입력하세요)"
        
        models = get_openrouter_model_list(api_key)
        
        # 기본 모델 선택 (Vision 지원 모델 우선)
        default_models = ["openai/gpt-4o", "anthropic/claude-3-5-sonnet", "google/gemini-pro-vision"]
        default = None
        for preferred in default_models:
            if preferred in models:
                default = preferred
                break
        
        if not default:
            default = models[0] if models and not models[0].startswith("❌") else "openai/gpt-4o"
        
        return gr.update(choices=models, value=default), default

    # === 이벤트 연결 ===
    api_key_input.change(lambda k: k, inputs=api_key_input, outputs=api_key_state)
    api_key_input.change(fn=update_models, inputs=api_key_input, outputs=[model_dropdown, model_state])
    model_dropdown.change(lambda m: m, inputs=model_dropdown, outputs=model_state)
    system_prompt_input.change(lambda p: p, inputs=system_prompt_input, outputs=system_prompt_state)

    submit_btn.click(
        fn=submit_message,
        inputs=[chat_state, image_input, user_input, api_key_state, system_prompt_state, model_state],
        outputs=[chat_state, chatbox, user_input]
    )

    user_input.submit(
        fn=submit_message,
        inputs=[chat_state, image_input, user_input, api_key_state, system_prompt_state, model_state],
        outputs=[chat_state, chatbox, user_input]
    )

    reset_btn.click(
        fn=reset_chat,
        inputs=[],
        outputs=[chat_state, chatbox]
    )

# === 실행 ===
if __name__ == "__main__":
    print("OpenRouter 기반 웹 앱 실행 중...", flush=True)
    demo.launch(share=True)