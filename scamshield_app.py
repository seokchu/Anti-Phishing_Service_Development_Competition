import streamlit as st
import re
import time
from datetime import datetime

# ==========================================
# 1. ScamShield v8.3 Logic Engine (Simplified)
# ==========================================

class MetaScorerV83:
    """
    ScamShield v8.3 Meta Scorer (Simplified for Prototype)
    """
    WHITELIST = {
        '1301': '검찰청',
        '112': '경찰청',
        '1332': '금융감독원',
        '118': 'KISA 불법스팸신고센터',
    }

    WEIGHTS = {
        'sender_unknown': 18,
        'sender_shortcode': 10,
        'not_in_contacts': 15,
        'first_contact': 10,
        'contains_url': 12,
        'contains_phone': 7,
        'financial_keywords_high': 10,
        'financial_keywords_low': 5,
        'urgency_keywords_high': 6,
    }
    
    MAX_SCORE = 70
    FINANCIAL_KEYWORDS = ['계좌', '이체', '입금', '송금', '대출', '카드', '결제', '은행', '금융', '출금', '돈', '명의', '도용', '범죄', '수사']
    URGENCY_KEYWORDS = ['급히', '즉시', '바로', '지금', '빨리', '긴급', '당장', '서둘러']

    def __init__(self):
        self.url_pattern = re.compile(r'http[s]?://|www\\.|bit\\.ly|\\.[a-z]{2,3}/')
        self.phone_pattern = re.compile(r'010[-\\s]?\\d{4}[-\\s]?\\d{4}|080[-\\s]?\\d{3,4}[-\\s]?\\d{4}|1588[-\\s]?\\d{4}')

    def calculate_score(self, text, meta):
        sender = meta.get('sender_number', '').replace('-', '')
        is_official = sender in self.WHITELIST
        has_url = bool(self.url_pattern.search(text))
        
        score = 0
        breakdown = {}
        reasons = []

        # [v8.3 Whitelist Benefit]
        if is_official:
            official_name = self.WHITELIST[sender]
            reasons.append(f"✅ {official_name}({sender}) 공식 번호 인증됨 (위험도 감면)")
            # No penalties for official numbers
        else:
            # [Case 2 Penalty]
            score += self.WEIGHTS['sender_unknown']
            breakdown['발신자(모름)'] = self.WEIGHTS['sender_unknown']
            reasons.append(f"⚠️ 모르는 번호({sender}): +{self.WEIGHTS['sender_unknown']}점")

            score += self.WEIGHTS['not_in_contacts']
            breakdown['미등록'] = self.WEIGHTS['not_in_contacts']
            reasons.append(f"⚠️ 연락처 미등록: +{self.WEIGHTS['not_in_contacts']}점")

            score += self.WEIGHTS['first_contact']
            breakdown['첫연락'] = self.WEIGHTS['first_contact']
            reasons.append(f"⚠️ 첫 연락: +{self.WEIGHTS['first_contact']}점")

        # [Common Content Analysis]
        if has_url:
            score += self.WEIGHTS['contains_url']
            breakdown['URL포함'] = self.WEIGHTS['contains_url']
            reasons.append("⚠️ URL 포함: +12점")
        
        financial_count = len([k for k in self.FINANCIAL_KEYWORDS if k in text])
        if financial_count >= 1:
            points = self.WEIGHTS['financial_keywords_high'] if financial_count >= 2 else self.WEIGHTS['financial_keywords_low']
            score += points
            breakdown['금융키워드'] = points
            reasons.append(f"⚠️ 금융 키워드({financial_count}개): +{points}점")

        score = min(score, self.MAX_SCORE)
        
        return {
            'total_score': score,
            'breakdown': breakdown,
            'reasons': reasons,
            'is_impersonation': False, # Disabled simple impersonation jump for User's scenario
            'is_safe_official': is_official and not has_url
        }

class ScamShieldSimulator:
    def __init__(self):
        self.meta_scorer = MetaScorerV83()

    def analyze(self, text, sender_number):
        # Allow simplified simulation: If text looks like phishing, give high AI score
        ai_score = 0
        if any(k in text for k in ['검찰', '계좌', '송금', '명의', '도용']):
            ai_score = 28 # High AI Score for phishing-like text
        
        meta_result = self.meta_scorer.calculate_score(text, {'sender_number': sender_number})
        
        if meta_result.get('is_impersonation'):
            final_score = 100
            ai_score = 30
        elif meta_result.get('is_safe_official'):
            final_score = 0
            ai_score = 0
        else:
            final_score = min(ai_score + meta_result['total_score'], 100)
            
        return {
            'final_score': final_score,
            'ai_score': ai_score,
            'meta_score': meta_result['total_score'],
            'reasons': meta_result['reasons'],
            'breakdown': meta_result.get('breakdown', {}),
            'grade': self.get_grade(final_score)
        }

    def get_grade(self, score):
        if score >= 75: return "🚨 긴급 (CRITICAL)"
        if score >= 50: return "🟠 위험 (DANGER)"
        if score >= 25: return "🟡 주의 (WARNING)"
        return "🟢 안전 (SAFE)"

# ==========================================
# 2. Streamlit UI
# ==========================================

st.set_page_config(page_title="ScamShield v8.3 Prototype", layout="wide")

st.title("🛡️ ScamShield v8.3 프로토타입")
st.markdown("### 검찰청 사칭 시나리오 시뮬레이션")

# --- Scenario Controls ---
with st.expander("🛠️ 시나리오 설정 (개발자 모드)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        scenario_type = st.radio(
            "시나리오 선택",
            ("직접 입력", "Case 1: 공식 번호 (1301)", "Case 2: 개인 번호 (010)"),
            index=1
        )
    
    with col2:
        # Default values based on scenario
        default_sender = "1301"
        default_text = "[검찰청] 귀하의 명의가 도용되어 대포통장이 개설되었습니다. 2023형제5938 사건 관련하여 긴급히 조사가 필요합니다."
        
        if scenario_type == "Case 2: 개인 번호 (010)":
            default_sender = "010-1234-5678"
            default_text = "[검찰청] 귀하의 명의가 도용되어 대포통장이 개설되었습니다. 아래 링크로 접속하여 사건 내용을 확인하시기 바랍니다. http://fa.ke/check"
        elif scenario_type == "Case 1: 공식 번호 (1301)":
            # Let user toggle URL for Case 1 to show Safe vs Impersonation
            include_url = st.checkbox("악성 URL 포함 (사칭 시나리오)", value=True)
            if include_url:
                default_text += " http://fa.ke/check"
            else:
                 default_text = "[검찰청] 귀하의 사건(2023형제5938)이 접수되었습니다. 담당 검사실 배정 후 연락드리겠습니다."

        sender_number = st.text_input("발신 번호", value=default_sender)
        message_text = st.text_area("메시지 내용", value=default_text)

# --- Analysis Logic ---
simulator = ScamShieldSimulator()
if st.button("📩 메시지 수신 (분석 시작)", type="primary"):
    with st.spinner("ScamShield AI가 메시지를 분석 중입니다..."):
        time.sleep(1.5) # Simulate processing time
        result = simulator.analyze(message_text, sender_number)
    
    st.divider()
    
    # --- Dual View UI ---
    col_user, col_guardian = st.columns(2)
    
    # [Left] User's Phone View
    with col_user:
        st.subheader("📱 사용자 휴대폰 (수신 화면)")
        st.info(f"📩 **[문자 수신]**\n\n**발신**: {sender_number}\n\n{message_text}")
        
        # Overlay Result
        st.markdown("---")
        if result['final_score'] >= 50:
            st.error(f"### {result['grade']}")
            st.write(f"**점수**: {result['final_score']} / 100")
            st.warning("⚠️ **피싱 의심! 절대 링크를 누르거나 송금하지 마세요.**")
        else:
            st.success(f"### {result['grade']}")
            st.write("안전한 메시지입니다.")

        with st.expander("상세 분석 결과 보기"):
            st.write(f"**AI 점수**: {result['ai_score']}점")
            st.write(f"**메타 점수**: {result['meta_score']}점")
            st.write("**판단 근거**:")
            for reason in result['reasons']:
                st.write(f"- {reason}")

    # [Right] Guardian's Phone View
    with col_guardian:
        st.subheader("🔔 보호자 휴대폰 (알림 화면)")
        
        if result['final_score'] >= 50:
            # Danger Alert
            container = st.container(border=True)
            container.markdown("### 🚨 [긴급] 가족 보호 알림")
            container.markdown(f"**부모님(사용자)** 휴대폰으로 **고위험 피싱 의심 문자**가 수신되었습니다.")
            
            st.markdown("#### 🛡️ 탐지된 위험 요소")
            for reason in result['reasons']:
                st.markdown(f"- ⚠️ {reason}")
            
            st.markdown("#### 💡 보호자 조치 가이드")
            st.info("1. 부모님께 즉시 전화를 걸어 상황을 확인하세요.\n2. URL을 클릭하지 말라고 당부하세요.\n3. 112 또는 1301에 신고하도록 도와주세요.")
            
            if st.button("📞 부모님께 전화 걸기"):
                st.toast("통화 연결 중...", icon="📞")
        
        else:
            # Safe / No Alert (Simulated)
            st.container(border=True).write("\n\n(위험 상황이 아니므로 알림이 울리지 않습니다.)\n\n🟢 **상태: 안전**")

