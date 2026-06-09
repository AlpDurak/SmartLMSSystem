import streamlit as st
import os
from lms_scraper import LMSScraper
from document_parser import get_document_text
from ai_engine import AIEngine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Öğrenci Asistanı - LMS Otomasyonu", layout="wide")

st.title("🎓 Öğrenci Asistanı: Akıllı LMS Sistemi")
st.markdown("---")

# Initialize stateless scraper
scraper = LMSScraper()

# Sidebar for Login and API Key
with st.sidebar:
    st.header("🔑 Giriş Bilgileri")
    lms_user = st.text_input("Öğrenci No / Kullanıcı Adı", value=st.session_state.get('lms_user', ''))
    lms_pass = st.text_input("LMS Şifresi", type="password", value=st.session_state.get('lms_pass', ''))
    gemini_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get('gemini_key', ''))
    
    if st.button("Sisteme Bağlan"):
        if not lms_user or not lms_pass or not gemini_key:
            st.error("Lütfen tüm bilgileri doldurun.")
        else:
            with st.spinner("LMS'ye giriş test ediliyor..."):
                if scraper.login_test(lms_user, lms_pass):
                    st.session_state['lms_user'] = lms_user
                    st.session_state['lms_pass'] = lms_pass
                    st.session_state['gemini_key'] = gemini_key
                    ai = AIEngine(gemini_key)
                    st.session_state['ai'] = ai
                    st.session_state['active_model'] = ai.model_name
                    # Clear previous session data
                    for key in list(st.session_state.keys()):
                        if key.startswith("materials_") or key == "courses":
                            del st.session_state[key]
                    st.success(f"Bağlantı kuruldu! Aktif Model: {ai.model_name}")
                    st.rerun()
                else:
                    st.error("Giriş başarısız. Lütfen bilgilerinizi kontrol edin.")

# Main Content
if 'lms_user' in st.session_state and 'ai' in st.session_state:
    st.header("📚 Dersleriniz")
    
    if 'courses' not in st.session_state:
        with st.spinner("Tüm dersleriniz taranıyor (Geniş kapsamlı tarama)..."):
            st.session_state['courses'] = scraper.get_courses(
                st.session_state['lms_user'], 
                st.session_state['lms_pass']
            )
    
    courses = st.session_state.get('courses', [])
    
    if not courses:
        st.warning("Hiç ders bulunamadı. Lütfen giriş bilgilerinizi kontrol edin veya tekrar tarayın.")
        if st.button("🔄 Tekrar Tara"):
            del st.session_state['courses']
            st.rerun()
    else:
        st.info(f"Toplam {len(courses)} ders bulundu.")
        course_names = [c['name'] for c in courses]
        selected_course_name = st.selectbox("Bir ders seçin:", ["Seçiniz..."] + course_names)
        
        if selected_course_name != "Seçiniz...":
            selected_course = next(c for c in courses if c['name'] == selected_course_name)
            
            st.subheader(f"📖 {selected_course_name} Materyalleri")
            
            mat_key = f"materials_{selected_course['link']}"
            if mat_key not in st.session_state:
                with st.spinner("Ders içerikleri analiz ediliyor (Tüm bölümler taranıyor)..."):
                    st.session_state[mat_key] = scraper.get_materials(
                        st.session_state['lms_user'], 
                        st.session_state['lms_pass'],
                        selected_course['link']
                    )
            
            materials = st.session_state.get(mat_key, [])
            
            if not materials:
                st.warning("Bu derste henüz indirilebilir materyal bulunamadı.")
                if st.button("🔄 Materyalleri Yenile"):
                    del st.session_state[mat_key]
                    st.rerun()
            else:
                material_titles = [m['title'] for m in materials]
                selected_material_titles = st.multiselect("Analiz edilecek materyalleri seçin (Birden fazla seçebilirsiniz):", material_titles)
                
                if selected_material_titles:
                    selected_materials = [m for m in materials if m['title'] in selected_material_titles]
                    
                    st.markdown("---")
                    st.subheader("⚙️ İşlem Seçenekleri")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        do_summary = st.checkbox("Konu Özeti Oluştur", value=True)
                        do_exam = st.checkbox("Örnek Sınav Oluştur", value=True)
                    
                    with col2:
                        if do_exam:
                            difficulty = st.select_slider("Sınav Zorluğu", options=["Kolay", "Orta", "Zor"])
                        else:
                            st.write("")
                    
                    if st.button("🚀 Başlat"):
                        if not do_summary and not do_exam:
                            st.warning("Lütfen en az bir işlem seçin.")
                        else:
                            with st.spinner("Materyaller indiriliyor ve işleniyor..."):
                                combined_text = ""
                                links_to_download = [mat['link'] for mat in selected_materials]
                                
                                downloaded_paths = scraper.download_materials(
                                    st.session_state['lms_user'], 
                                    st.session_state['lms_pass'],
                                    links_to_download
                                )
                                
                                for i, file_path in enumerate(downloaded_paths):
                                    if file_path:
                                        mat = selected_materials[i]
                                        text = get_document_text(file_path)
                                        if text.strip():
                                            combined_text += f"\n--- DOSYA: {mat['title']} ---\n{text}\n"
                                        
                                        if os.path.exists(file_path):
                                            os.remove(file_path)
                                
                                if not combined_text.strip():
                                    st.error("Seçilen dosyalardan metin çıkarılamadı.")
                                else:
                                    tabs = []
                                    if do_summary: tabs.append("📝 Konu Özeti")
                                    if do_exam: tabs.append("📝 Örnek Sınav")
                                    
                                    tab_objects = st.tabs(tabs)
                                    
                                    current_tab = 0
                                    if do_summary:
                                        with tab_objects[current_tab]:
                                            summary = st.session_state['ai'].summarize(combined_text)
                                            st.markdown(summary)
                                        current_tab += 1
                                    
                                    if do_exam:
                                        with tab_objects[current_tab]:
                                            exam = st.session_state['ai'].generate_exam(combined_text, difficulty)
                                            st.markdown(exam)

else:
    st.info("Sistemi kullanmak için sol taraftaki panelden giriş yapmanız gerekmektedir.")
    st.image("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", use_column_width=True)

st.markdown("---")
st.caption("Öğrenci Asistanı v1.2 | Işık Üniversitesi LMS Entegrasyonu")
