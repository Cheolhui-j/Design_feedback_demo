import gradio as gr
import base64
import datetime

import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration
from PIL import Image
import requests
from io import BytesIO

# === 1. 설정 및 모델 로드 ===
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device : {device}")

model_name = "llava-hf/llava-1.5-7b-hf"  # 모델명 (변경 가능)
system_prompt = "You're participating in an interview..."

# 모델 및 프로세서 로드
processor = AutoProcessor.from_pretrained(model_name)
model = LlavaForConditionalGeneration.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
)
model.to(device)

# 2-1. (선택 사항) Processor config 강제 수정
# 일부 버전의 LLaVA 모델에선 patch_size, vision_feature_select_strategy를 변경해야 할 수 있습니다.
# 필요 없으면 주석 처리하세요.
processor.patch_size = 14
processor.vision_feature_select_strategy = "default"

def load_image(image_path: str) -> Image.Image:
    """
    이미지 로드 함수: URL 또는 로컬 파일 경로 모두 처리.
    """
    try:
        if image_path.startswith("http"):
            response = requests.get(image_path)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert("RGB")
        else:
            image = Image.open(image_path).convert("RGB")
        return image
    except Exception as e:
        raise ValueError(f"이미지를 불러오는 중 오류 발생: {e}")

# === 2. 로컬 추론 함수 ===
def generate_response(image: Image.Image, prompt: str, chat_history=None):
    # 이전 대화 이력을 프롬프트에 포함
    context_pairs = []
    if chat_history:
        for i in range(0, len(chat_history)-1, 2):
            if i+1 < len(chat_history):
                user_msg = chat_history[i][1]
                ai_msg = chat_history[i+1][1]
                context_pairs.append(f"사용자: {user_msg}\nAI: {ai_msg}")
    
    context = "\n".join(context_pairs)

    # 2) 프롬프트에 <image> 토큰 삽입
    #    LLaVA는 텍스트 안에 이 토큰이 있어야 "이미지 1장"을 인식합니다.
    prompt_with_image = f"<image>\n{prompt}"
    
    # 현재 사용자 메시지 추가
    full_prompt = (
        f"{system_prompt}\n\n"
        f"이전 대화 내용:\n{context}\n\n"
        f"사용자: {prompt_with_image}\nAI:"
    )
    
    # 이미지와 텍스트 입력 준비
    inputs = processor(
        text=full_prompt,
        images=image,
        return_tensors="pt"
    ).to(device)
    
    # 생성 파라미터 설정
    generation_config = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "do_sample": True,
    }
    
    # 추론 실행
    with torch.inference_mode():
        output = model.generate(**inputs, **generation_config)
    
    # 생성된 텍스트 디코딩
    generated_text = processor.decode(output[0], skip_special_tokens=True)
    
    # 시스템 프롬프트와 입력 제거하여 응답만 추출
    response = generated_text.split("AI:")[-1].strip()
    
    return response

# === 3. 채팅 처리 함수 ===
def chat_with_model(chat_history, image: Image.Image, user_message: str):
    if not user_message.strip():
        return chat_history, ""  # 빈 입력은 무시하고 입력창 비우기
    
    # 채팅 기록에 사용자 메시지 추가
    chat_history.append(("사용자", user_message))
    
    if not image:
        chat_history.append(("AI", "❌ 이미지를 반드시 업로드해주세요."))
        return chat_history, ""
    
    try:
        # 로컬 모델로 추론 실행
        bot_response = generate_response(image, user_message, chat_history)
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
    gr.Markdown("## 💬 디자인 피드백 웹 앱 Demo (로컬 LLaVa 추론)")
    
    # 모델 정보 표시
    gr.Markdown(f"**모델 정보**: {model_name} | 실행 환경: {device}", elem_classes="model-info")
    
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
        now = datetime.datetime.now()
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
if __name__ == "__main__":
    print(f"모델을 로드했습니다: {model_name}")
    print(f"실행 환경: {device}")
    demo.launch(share=True)

# import torch
# from transformers import AutoProcessor, LlavaForConditionalGeneration
# from PIL import Image
# import requests
# from io import BytesIO

# # 1. 디바이스 설정
# device = "cuda" if torch.cuda.is_available() else "cpu"
# print(f"Using device: {device}")

# # 2. 모델 & 프로세서 설정
# #   - 원하는 LLaVA 모델 경로로 변경하세요. (예: "llava-hf/llava-1.5-7b-hf")
# model_id = "llava-hf/llava-1.5-7b-hf"

# # Processor & Model 로드
# processor = AutoProcessor.from_pretrained(model_id)
# #   - device=='cuda'일 때 float16, CPU일 때 float32
# model = LlavaForConditionalGeneration.from_pretrained(
#     model_id, 
#     torch_dtype=torch.float16 if device == "cuda" else torch.float32
# )
# model.to(device)

# # 2-1. (선택 사항) Processor config 강제 수정
# # 일부 버전의 LLaVA 모델에선 patch_size, vision_feature_select_strategy를 변경해야 할 수 있습니다.
# # 필요 없으면 주석 처리하세요.
# processor.patch_size = 14
# processor.vision_feature_select_strategy = "default"

# def load_image(image_path: str) -> Image.Image:
#     """
#     이미지 로드 함수: URL 또는 로컬 파일 경로 모두 처리.
#     """
#     try:
#         if image_path.startswith("http"):
#             response = requests.get(image_path)
#             response.raise_for_status()
#             image = Image.open(BytesIO(response.content)).convert("RGB")
#         else:
#             image = Image.open(image_path).convert("RGB")
#         return image
#     except Exception as e:
#         raise ValueError(f"이미지를 불러오는 중 오류 발생: {e}")

# def generate_answer(image_path: str, prompt: str) -> str:
#     """
#     LLaVA 모델에게 '이미지 + 텍스트'를 입력하여 문장을 생성하는 함수.
#     """
#     # 1) 이미지 로드
#     image = load_image(image_path)

#     # 2) 프롬프트에 <image> 토큰 삽입
#     #    LLaVA는 텍스트 안에 이 토큰이 있어야 "이미지 1장"을 인식합니다.
#     prompt_with_image = f"<image>\n{prompt}"
    
#     # 2) processor로 이미지+텍스트 전처리
#     #    LLaVA의 AutoProcessor가 'pixel_values'와 'input_ids' 등을 구성해줌
#     inputs = processor(
#         text=prompt_with_image,
#         images=image,
#         return_tensors="pt"
#     )

#     # 3) device로 이동
#     inputs = {k: v.to(device) for k, v in inputs.items()}
    
#     # 4) 생성 파라미터 설정
#     generation_kwargs = dict(
#         max_new_tokens=256,
#         do_sample=False,
#         temperature=0.1,
#         top_p=0.95
#     )

#     # 5) 추론 실행
#     with torch.no_grad():
#         output_ids = model.generate(**inputs, **generation_kwargs)

#     # 6) 결과 디코딩
#     #    processor.decode(...)로 ID를 문자열로 변환.
#     #    (LLaVA는 대체로 "prompt + 답변" 형태로 결과가 나올 수 있음)
#     generated_text = processor.decode(output_ids[0], skip_special_tokens=True)
    
#     print("Raw generated_text:", repr(generated_text))

#     # 7) prompt가 결과에 포함되어 있으면 제거(필요한 경우)
#     #    간혹 모델이 "prompt + 답변" 통째로 출력하기도 하므로 처리
#     if prompt in generated_text:
#         answer = generated_text.split(prompt, 1)[-1].strip()
#     else:
#         answer = generated_text.strip()

#     return answer

# if __name__ == "__main__":
#     # 테스트 이미지 경로 (URL 혹은 로컬 파일)
#     image_path = "test.jpeg"  
#     # image_path = "https://example.com/image.jpg"

#     # 질문 프롬프트
#     prompt = "What do you see in this image? Please elaborate."

#     # 추론 실행
#     answer = generate_answer(image_path, prompt)
#     print("모델 응답:", answer)
