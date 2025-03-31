import gradio as gr
import requests
import base64
from PIL import Image
from io import BytesIO
import json

# === 1. 설정 ===
llava_api_url = "http://192.168.11.181:11434/api/generate"
llava_model_name = "llava"
llava_system_prompt = "You're participating in an interview..."

# === 2. 이미지 → base64 인코딩 ===
def encode_image_to_base64(pil_image: Image.Image):
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# === 3. 채팅 처리 함수 ===
def chat_with_model(chat_history, image: Image.Image, user_message: str):
    if not user_message.strip():
        return chat_history, ""  # 빈 입력은 무시하고 입력창 비우기
    
    # 채팅 기록에 사용자 메시지 추가
    chat_history.append(("사용자", user_message))
    
    if not image:
        chat_history.append(("AI", "❌ 이미지를 반드시 업로드해주세요."))
        return chat_history, ""
    
    # 이미지 base64 인코딩
    encoded_image = encode_image_to_base64(image)
    
    # 이전 대화 이력을 프롬프트에 포함 (개선된 방식)
    # 마지막에 추가된 현재 사용자 메시지는 제외하고 이전 대화만 포함
    context_pairs = []
    for i in range(0, len(chat_history)-1, 2):  # 사용자와 AI 응답이 쌍을 이루므로 2씩 증가
        if i+1 < len(chat_history):  # AI 응답이 있는지 확인
            user_msg = chat_history[i][1]
            ai_msg = chat_history[i+1][1]
            context_pairs.append(f"사용자: {user_msg}\nAI: {ai_msg}")
    
    context = "\n".join(context_pairs)
    
    # 현재 사용자 메시지 추가
    full_prompt = (
        f"{llava_system_prompt}\n\n"
        f"이전 대화 내용:\n{context}\n\n"
        f"사용자: {user_message}\nAI:"
    )
    
    payload = {
        "model": llava_model_name,
        "prompt": full_prompt,
        "images": [encoded_image],
        "stream": False
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(llava_api_url, headers=headers, data=json.dumps(payload), stream=True)
        if response.ok:
            bot_response = response.json().get("response", "(빈 응답)")
        else:
            bot_response = f"❌ 오류 {response.status_code}: {response.text}"
    except Exception as e:
        bot_response = f"❌ 예외 발생: {e}"
    
    # 응답 추가
    chat_history.append(("AI", bot_response))
    return chat_history, ""  # 두 번째 반환값은 입력창 비우기

# === 4. UI 구성 ===
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
""") as demo:
    gr.Markdown("## 💬 디자인 피드백 웹 앱 Demo")
    
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
    
    # 현재 시간을 반환하는 함수
    def get_current_time():
        from datetime import datetime
        now = datetime.now()
        return now.strftime("%p %I:%M").lower()  # 오전/오후 시:분
    
    # 대화 초기화 함수
    def reset_chat():
        return [], "<div class='chatbox'><div class='history-indicator'>이전 대화 기록이 모델에 전달됩니다</div></div>"
    
    # 대화 렌더링 함수
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
                </div>
                """
            else:  # AI
                messages_html += f"""
                <div class='message ai-msg'>
                    <div class='profile'></div>
                    <div>
                        <div class='sender'>AI 도우미</div>
                        <div class='bubble ai-bubble'>{msg}</div>
                        <div class='time'>{current_time}</div>
                    </div>
                </div>
                """
        
        return f"<div class='chatbox'>{messages_html}</div>"
    
    # 메시지 제출 함수
    def submit_message(chat_state, image, message):
        if not message.strip():
            return chat_state, render_chat(chat_state), ""
        
        new_history, _ = chat_with_model(chat_state, image, message)
        return new_history, render_chat(new_history), ""
    
    # 이벤트 연결
    submit_btn.click(
        fn=submit_message,
        inputs=[chat_state, image_input, user_input],
        outputs=[chat_state, chatbox, user_input]
    )
    
    user_input.submit(
        fn=submit_message,
        inputs=[chat_state, image_input, user_input],
        outputs=[chat_state, chatbox, user_input]
    )
    
    reset_btn.click(
        fn=reset_chat,
        inputs=[],
        outputs=[chat_state, chatbox]
    )

# 서버 실행
demo.launch()