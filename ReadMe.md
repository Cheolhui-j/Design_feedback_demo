# 💬 GPT-4o 기반 디자인 피드백 웹앱 (모델 선택 기능 포함)

이 프로젝트는 OpenAI의 GPT-4o 및 기타 GPT 모델을 활용하여 **디자인 이미지에 대한 자연어 피드백을 제공하는 Gradio 웹앱**입니다.  
사용자는 이미지와 질문을 입력하고, **API 키, System Prompt, 모델 종류**를 직접 선택하여 테스트할 수 있습니다.

---

## 🚀 주요 기능

| 기능                         | 설명 |
|------------------------------|------|
| ✅ GPT 기반 멀티모달 응답 | 이미지 + 텍스트를 입력받아 응답 생성 |
| 🔑 API 키 직접 입력          | OpenAI API 키를 웹에서 입력 |
| 🛠️ System Prompt 입력 가능   | AI 역할/행동을 커스터마이징 가능 |
| 🤖 모델 선택 드롭다운        | gpt-4o, gpt-4-turbo, gpt-3.5-turbo 등 실험 가능 |
| 💬 채팅 히스토리 유지        | 대화 맥락이 유지되어 응답 품질 향상 |
| 🔁 대화 초기화               | 대화 초기화 버튼 포함 |

---

## 📦 설치 및 실행

```bash
git clone https://github.com/your-id/gpt4o-feedback-app.git
cd gpt4o-feedback-app

pip install -r requirements.txt
python app.py
```

> 🔧 `requirements.txt` 예시:
> ```
> gradio
> openai
> pillow
> ```

---

## 🐳 Dockerfile을 기반으로 실행하는 방법 (권장)

이 프로젝트는 Docker 이미지를 빌드한 후

```bash
docker build -t gpt-conda-app <Dockerfile 경로>
```

`app.py`와 같은 실행 파일을 **컨테이너 실행 시에 외부에서 mount** 하여 사용합니다.

```bash
docker run --rm -it \
  -v <프로젝트 경로>/app.py:/app/app.py \
  gpt-conda-app app.py
```

## 🛠 사용 방법

1. **API 키 입력**  
   [OpenAI API 키 만들기](https://platform.openai.com/settings/organization/api-keys)

2. **System Prompt 입력 (선택)**  
   예: `You are a helpful UX designer giving feedback on visual layout.`

3. **모델 선택**  
   예: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo` 등

4. **이미지 업로드 + 질문 입력 → 전송**

---

## 💡 예시 Prompt

```text
You are a professional UI designer. Please give detailed feedback on layout, spacing, and font usage in this image.
```

---

## 🧪 테스트 예시

- 버튼이 너무 작아 보이나요?
- 폰트 간격이 어색한가요?
- 어떤 색상 조합이 더 나을까요?

---

## 🧩 향후 개선 방향

- [ ] 채팅 저장/불러오기 기능
- [ ] 개선점을 적용한 UI 이미지 생성
- [ ] 다대일 채팅 지원

---

## 📌 주의사항

- 무료 요금제는 이미지 입력 및 응답이 제한될 수 있습니다.
- 이미지 해상도는 너무 크지 않도록 조절 (ex: 1024x1024 이하 권장)
- gpt-3.5 계열의 경우 테스트 시 에러가 발생하므로 가급적 gpt-4이후 버전을 사용하길 권장합니다.

---