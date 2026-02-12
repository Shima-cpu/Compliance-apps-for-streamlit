# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(
    page_title="🧰 Tools: Passport + Compliance",
    page_icon="🧰",
    layout="centered",
)

# =========================================================
# 1) PASSPORT TOOL
# =========================================================

MIN_BIRTH = date(1900, 1, 1)
MAX_BIRTH = date.today()
MIN_ISSUE = date(1900, 1, 1)
MAX_ISSUE = date.today()


def safe_add_years(d: date, years: int) -> date:
    """Добавить годы к дате, корректно обрабатывая 29 февраля."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + years)


def current_passport_stage(birth: date, issue: date) -> int | None:
    """
    Определить этап текущего паспорта по дате выдачи (по интервалам возрастных порогов):
    возвращает 14, 20, 45 или None (если ввод странный).
    """
    d14 = safe_add_years(birth, 14)
    d20 = safe_add_years(birth, 20)
    d45 = safe_add_years(birth, 45)

    if issue >= d45:
        return 45
    if d20 <= issue < d45:
        return 20
    if d14 <= issue < d20:
        return 14
    return None


def classify_passport_stage_text(stage: int | None) -> str:
    if stage == 14:
        return "Первичное получение в 14 лет"
    if stage == 20:
        return "Обмен в 20 лет"
    if stage == 45:
        return "Обмен в 45 лет"
    return "Не удалось однозначно определить (проверьте ввод)"


def compute_status(birth: date, issue: date, today: date) -> dict:
    """
    Возвращает:
      stage_label, next_change, deadline,
      status_kind: 'invalid' | 'due' | 'ok' | 'no_more',
      days_left (если применимо).
    """
    d20 = safe_add_years(birth, 20)
    d45 = safe_add_years(birth, 45)

    stage = current_passport_stage(birth, issue)
    stage_label = classify_passport_stage_text(stage)

    # Следующая возрастная замена по текущему возрасту (устойчивый фолбэк)
    if today < d20:
        age_next_change = d20
    elif today < d45:
        age_next_change = d45
    else:
        age_next_change = None

    if stage == 45:
        return {
            "stage_label": stage_label,
            "next_change": None,
            "deadline": None,
            "status_kind": "no_more",
            "days_left": None,
        }

    if stage == 20:
        next_change = d45
    elif stage == 14:
        next_change = d20
    else:
        # если не смогли определить стадию по issue — ориентируемся по возрасту
        next_change = age_next_change

    if next_change is None:
        return {
            "stage_label": stage_label,
            "next_change": None,
            "deadline": None,
            "status_kind": "no_more",
            "days_left": None,
        }

    deadline = next_change + timedelta(days=90)

    if today > deadline:
        status_kind = "invalid"
        days_left = None
    elif today >= next_change:
        status_kind = "due"
        days_left = (deadline - today).days
    else:
        status_kind = "ok"
        days_left = (next_change - today).days

    return {
        "stage_label": stage_label,
        "next_change": next_change,
        "deadline": deadline,
        "status_kind": status_kind,
        "days_left": days_left,
    }


def validate_inputs(birth: date, issue: date, today: date) -> list[str]:
    errs: list[str] = []

    if birth > today:
        errs.append("Дата рождения не может быть в будущем.")
    if issue > today:
        errs.append("Дата выдачи паспорта не может быть в будущем.")
    if issue < birth:
        errs.append("Дата выдачи паспорта не может быть раньше даты рождения.")

    if relativedelta(today, birth).years < 14:
        errs.append("Лицу младше 14 лет паспорт ещё не выдается.")

    d14 = safe_add_years(birth, 14)
    if issue < d14:
        errs.append("Паспорт не может быть выдан ранее достижения 14 лет. Проверьте дату выдачи.")

    if not (MIN_BIRTH <= birth <= MAX_BIRTH):
        errs.append(
            f"Дата рождения должна быть в диапазоне "
            f"{MIN_BIRTH.strftime('%d.%m.%Y')}–{MAX_BIRTH.strftime('%d.%m.%Y')}."
        )
    if not (MIN_ISSUE <= issue <= MAX_ISSUE):
        errs.append(
            f"Дата выдачи должна быть в диапазоне "
            f"{MIN_ISSUE.strftime('%d.%m.%Y')}–{MAX_ISSUE.strftime('%d.%m.%Y')}."
        )

    return errs


def passport_app():
    st.title("🛂 Калькулятор замены паспорта РФ")
    st.caption("Рассчитывает даты обязательной замены по порогам 20 и 45 лет и 90-дневному сроку после дня рождения.")

    with st.expander("Правовая основа (кратко)"):
        st.markdown(
            "- Паспорт гражданина РФ выдаётся в 14 лет и подлежит замене при достижении 20 и 45 лет.\n"
            "- На замену обычно предоставляется 90 календарных дней после соответствующего дня рождения.\n"
            "⚠️ Учитывайте, что локальные правила/исключения (например, замена за рубежом) могут меняться."
        )

    today = date.today()
    col1, col2 = st.columns(2)
    with col1:
        birth = st.date_input(
            "Дата рождения",
            value=date(1990, 1, 1),
            min_value=MIN_BIRTH,
            max_value=MAX_BIRTH,
            format="DD.MM.YYYY",  # если старая версия Streamlit — удалите этот параметр
            key="passport_birth_v1",
        )
    with col2:
        issue = st.date_input(
            "Дата выдачи текущего паспорта",
            value=date(2010, 1, 1),
            min_value=MIN_ISSUE,
            max_value=MAX_ISSUE,
            format="DD.MM.YYYY",
            key="passport_issue_v1",
        )

    if st.button("Рассчитать", key="passport_calc_btn"):
        errors = validate_inputs(birth, issue, today)
        for e in errors:
            st.error(e)

        if not errors:
            age_years = relativedelta(today, birth).years
            st.subheader("Результаты")
            st.write(f"Возраст (полных лет): {age_years}")

            res = compute_status(birth, issue, today)
            st.write(f"Текущий документ получен как: {res['stage_label']}")

            if res["next_change"]:
                st.write(f"Дата обязательной замены: {res['next_change'].strftime('%d.%m.%Y')}")
                st.write(f"Крайний срок (90 дней после ДР): {res['deadline'].strftime('%d.%m.%Y')}")

            if res["status_kind"] == "invalid":
                st.error("Паспорт недействителен. Требуется замена.")
            elif res["status_kind"] == "due":
                st.warning(f"Требуется замена. До крайнего срока осталось {res['days_left']} дн.")
            elif res["status_kind"] == "ok":
                st.success(f"Паспорт действителен. До даты замены осталось {res['days_left']} дн.")
            elif res["status_kind"] == "no_more":
                st.info("Возрастных замен больше нет.")


# =========================================================
# 2) COMPLIANCE TEMPLATE TOOL
# =========================================================

intro_texts = {
    "Russian": """Добрый день,

в соответствии с требованиями регулятора FSC Белиза и законодательством по борьбе с отмыванием денежных средств RoboForex Ltd обязана на регулярной основе осуществлять постоянную проверку и мониторинг личной информации своих клиентов.""",
    "English": """Hello,

in accordance with the requirements of the FSC Belize regulator and anti-money laundering legislation, RoboForex Ltd is obliged to regularly verify and monitor the personal information of its clients."""
}

closing_texts = {
    "Russian": """Мы ценим ваше сотрудничество.

Если у вас есть какие-либо вопросы, пожалуйста, свяжитесь с нами.

С уважением,""",
    "English": """We appreciate your cooperation.

If you have any questions, please contact us.

Best regards,"""
}

blocks = {
    "SOF": {
        "Russian": {
            "lead": "В связи с этим, мы просим вас предоставить информацию об источнике средств, которые были зачислены на ваши торговые счета в RoboForex Ltd.",
            "add":  "Также, пожалуйста, предоставьте информацию об источнике средств, которые были зачислены на ваши торговые счета в RoboForex Ltd.",
            "final": "Помимо этого, пожалуйста, предоставьте информацию об источнике средств, которые были зачислены на ваши торговые счета в RoboForex Ltd.",
            "rest": "\n\nПрилагаем список документов, которые можно использовать для проверки происхождения средств.\n\nВы можете предоставить нам любые документы, такие как: справки о зарплате, налоговые декларации, доходы от бизнеса, продажи имущества и т. д. или любой другой документ, указанный в прилагаемом документе."
        },
        "English": {
            "lead": "In this regard, we ask you to provide information on the source of funds credited to your trading accounts with RoboForex Ltd.",
            "add":  "Additionally, please provide information on the source of funds credited to your trading accounts with RoboForex Ltd.",
            "final": "Moreover, please provide information on the source of funds credited to your trading accounts with RoboForex Ltd.",
            "rest": "\n\nAttached is a list of documents that can be used to verify the origin of funds.\n\nYou can provide us with any documents, such as salary certificates, tax returns, business income, property sales, etc., or any other document specified in the attached document."
        }
    },
    "ID": {
        "Russian": {
            "lead": "В связи с этим, мы просим вас предоставить скан или фото актуального паспорта, удостоверяющего вашу личность.",
            "add":  "Также, пожалуйста, предоставьте скан или фото актуального паспорта, удостоверяющего вашу личность.",
            "final": "Помимо этого, пожалуйста, предоставьте скан или фото актуального паспорта, удостоверяющего вашу личность.",
            "rest": ""
        },
        "English": {
            "lead": "In this regard, we ask you to provide a scan or photo of your valid passport or another identity document.",
            "add":  "Additionally, please provide a scan or photo of your valid passport or another identity document.",
            "final": "Moreover, please provide a scan or photo of your valid passport or another identity document.",
            "rest": ""
        }
    },
    "UB": {
        "Russian": {
            "lead": "В связи с этим, мы просим вас предоставить счёт за коммунальные услуги или банковскую выписку для подтверждения вашего адреса проживания.",
            "add":  "Также, пожалуйста, предоставьте счёт за коммунальные услуги или банковскую выписку для подтверждения вашего адреса проживания.",
            "final": "Помимо этого, пожалуйста, предоставьте счёт за коммунальные услуги или банковскую выписку для подтверждения вашего адреса проживания.",
            "rest": ""
        },
        "English": {
            "lead": "In this regard, we ask you to provide a utility bill or a bank statement to confirm your residential address.",
            "add":  "Additionally, please provide a utility bill or a bank statement to confirm your residential address.",
            "final": "Moreover, please provide a utility bill or a bank statement to confirm your residential address.",
            "rest": ""
        }
    }
}

PRIORITY = ["SOF", "ID", "UB"]


def sort_by_priority(keys):
    return [k for k in PRIORITY if k in keys]


def render_middle_adaptive(lang: str, reqs: list) -> str:
    ordered = sort_by_priority(reqs)
    parts = []
    for i, r in enumerate(ordered):
        seg = blocks[r][lang]
        if i == 0:
            first_sentence = seg["lead"]
        elif i == 1:
            first_sentence = seg["add"]
        else:
            first_sentence = seg["final"]
        parts.append((first_sentence + seg.get("rest", "")).strip())
    return "\n\n".join(parts)


def js_escape(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
         .replace("`", "\\`")
         .replace("${", "\\${")
         .replace("\r", "")
         .replace("\n", "\\n")
    )


def compliance_app():
    st.title("Compliance request template")

    selected_parts = st.multiselect(
        "Choose your request:",
        options=["SOF", "ID", "UB"],
        default=["SOF"],
        key="cmp_selected_parts",
    )

    language = st.radio(
        "Select request language:",
        list(intro_texts.keys()),
        key="cmp_language",
    )

    if st.button("Generate text", key="cmp_generate_btn"):
        if not selected_parts:
            placeholder_text = "Please choose request options" if language == "English" else "Пожалуйста, выберите опции запроса"
            st.text_area("Result:", placeholder_text, height=320, key="cmp_result_empty")
            return

        middle_text = render_middle_adaptive(language, selected_parts)
        text = f"{intro_texts[language]}\n\n{middle_text}\n\n{closing_texts[language]}".strip()

        st.text_area("Result:", text, height=320, key="cmp_result")

        components.html(
            f"""
            <button id="copyButton">Copy text</button>
            <script>
                document.getElementById('copyButton').addEventListener('click', function() {{
                    const text = `{js_escape(text)}`;
                    navigator.clipboard.writeText(text).then(function() {{
                        alert('Text copied to clipboard!');
                    }}).catch(function(err) {{
                        alert('Error copying text!');
                    }});
                }});
            </script>
            """,
            height=100
        )


# =========================================================
# MAIN: TABS
# =========================================================

tab1, tab2 = st.tabs(["🛂 Паспорт РФ", "🧾 Compliance templates"])
with tab1:
    passport_app()
with tab2:
    compliance_app()
