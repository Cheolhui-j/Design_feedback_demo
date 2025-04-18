
# 💬 GPT-4o 기반 디자인 피드백 웹앱

이 프로젝트는 OpenAI의 GPT-4o 멀티모달 모델을 활용하여 **업로드된 이미지에 대해 자연어 기반 피드백을 제공하는 Gradio 웹앱**입니다.  
사용자는 이미지와 질문을 입력하고, **API 키 및 시스템 프롬프트(System Prompt)**를 직접 설정할 수 있습니다.

---

## 🚀 데모 기능 요약

| 기능                         | 설명 |
|------------------------------|------|
| ✅ GPT-4o 기반 멀티모달 응답 | 이미지 + 텍스트를 함께 입력 받아 분석 |
| 🔑 API 키 직접 입력          | 사용자의 OpenAI API 키를 통해 요청 처리 |
| 🛠️ System Prompt 입력 가능   | 원하는 도우미 역할을 설정할 수 있음 |
| 💬 채팅 히스토리 유지        | 이전 대화가 모델에게 전달되어 맥락 유지 |
| 🖼️ 이미지 업로드             | JPG/PNG 등 업로드하여 질문 가능 |
| 🔁 대화 초기화 기능 포함      | 대화 기록을 리셋할 수 있음 |

---

## 📦 설치 및 실행 방법

### 1. Python 설치
```bash
python --version  # Python 3.8 이상 확인
```

### 2. 프로젝트 클론 및 패키지 설치
```bash
git clone https://github.com/your-id/your-repo.git
cd your-repo

pip install -r requirements.txt
```

> requirements.txt 예시:
> ```text
> gradio
> openai
> pillow
> ```

### 3. 앱 실행
```bash
python app.py
```

실행 후 브라우저에서 `http://localhost:7860` 자동 열림

---

## 🛠 사용 방법

1. **OpenAI API 키 입력**
   - [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) 에서 생성한 키 입력

2. **System Prompt 작성 (선택)**
   - 예: `You are a UX/UI design expert giving feedback to junior designers.`

3. **디자인 이미지 업로드**

4. **질문 입력**
   - 예: `이 버튼 위치는 괜찮나요?`, `더 좋은 폰트 추천해줘.`

5. **전송 버튼 클릭**

---

## 💡 예시 System Prompt

```text
You are a professional UX/UI designer. Provide constructive, helpful, and detail-oriented feedback about the user's uploaded design image.
```

---

## 📌 주의사항

- GPT-4o는 **이미지 입력을 지원하는 최신 모델**입니다. 반드시 해당 모델이 활성화된 API 키를 사용하세요.
- 무료 요금제는 이미지 입력이 제한될 수 있습니다.
- 이미지 해상도는 너무 크지 않도록 조절 (ex: 1024x1024 이하 권장)

---

## 📷 예시 화면

> 이미지 미리보기, 채팅 UI 예시 등 첨부 가능 (원하는 경우 샘플 이미지도 제공해드릴게요)

---

## 🧩 향후 개선 방향

- [ ] 채팅 저장/불러오기 기능
- [ ] 파일 첨부 및 문맥 확장 (텍스트+이미지)
- [ ] 개선된 디자인 이미지 생성
- [ ] 다대일 채팅 지원

---
