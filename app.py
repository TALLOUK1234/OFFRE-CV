import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import plotly.graph_objects as go
import time
import matplotlib.pyplot as plt
from Coures import ds_course

# Charger les variables d'environnement
load_dotenv()
genai_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=genai_key)

# Fonction pour obtenir une réponse de l'API Gemini
def get_gemini_response(prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text

# Fonction pour extraire le texte d'un fichier PDF
def get_pdf_text(uploaded_file):
    pdf_reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += str(page.extract_text())
    return text

# Prompts pour l'API Gemini
input_prompt_compare = """
Hey Act Like a skilled resume parser with a deep understanding of tech field, software engineering,
data science, data analyst, and big data engineer. Your task is to extract the skills from the resume 
and compare them with the skills required in the job description. Provide a percentage match and 
list any missing skills from the resume.

resume:{text}
description:{jd}

I want the response in the following structure:
"Match": "0.57",
"MissingSkills": ["skill1", "skill2"],
"Skills": ["skill3", "skill4"]
"""

# Application Streamlit
st.title("Hello dear candidate In Your App Skills matcher Gen AI")
st.sidebar.image("images/logo_nlp.png", use_column_width=True)
st.sidebar.markdown('<p style="font-size: 16px; color: #555; text-align: center;">Created by Said Tallouk</p>', unsafe_allow_html=True)
jd = st.text_area("Job Description for the Role")
uploaded_file = st.file_uploader("Upload your Resume", type="pdf", help="Upload your Resume here")
submit = st.button("Submit")

# Fonctions pour analyser les réponses de l'API
def parse_response_compare(response_string):
    try:
        response_data = {}
        lines = response_string.split('\n')
        for line in lines:
            if 'Match' in line:
                response_data['Match'] = line.split(': ')[1].strip().strip('"').strip(',')
            elif 'MissingSkills' in line:
                skills = line.split(': ')[1].strip().strip('[]').replace('"', '').split(', ')
                response_data['MissingSkills'] = skills
            elif 'Skills' in line:
                skills = line.split(': ')[1].strip().strip('[]').replace('"', '').split(', ')
                response_data['Skills'] = skills
        return response_data
    except Exception as e:
        print("Error parsing response string:", e)
        return None

# Fonction pour créer un diagramme à jauge
def plot_gauge(similarity_score):
    # Initialiser la progression à 0
    progress = 0

    # Créer le graphique Plotly
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=progress,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Match with offer"},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': 'darkblue'}, 
            'steps': [
                {'range': [0, 25], 'color': "lightgray"},
                {'range': [25, 50], 'color': "lightgray"},
                {'range': [50, 75], 'color': "lightgray"},
                {'range': [75, 100], 'color': "lightgray"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.90,
                'value': progress}},
        number={'suffix': "%" 
        }
    ))

    # Afficher le graphique
    chart = st.plotly_chart(fig)

    # Boucle pour simuler l'augmentation du score de correspondance
    while progress <= similarity_score * 100:
        time.sleep(0.1)
        progress += 1 
        fig.update_traces(value=progress)
        chart.plotly_chart(fig, use_container_width=True)

# Fonction pour créer un diagramme en secteurs (Donut Chart)
def plot_donut_chart(similarity_score):
    labels = ['Cv Matcher', 'Difference with offer']
    values = [similarity_score, 1 - similarity_score]

    plt.figure(figsize=(8, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
    plt.title('Similarité entre les compétences du CV et de l\'offre d\'emploi')
    plt.axis('equal')  # Pour que le diagramme soit un cercle

    st.pyplot(plt)

# Fonction pour formater la réponse
def format_response_compare(response):
    if response:
        match = response.get("Match")
        match = match.strip('"')
        missing_skills = response.get("MissingSkills", [])
        skills = response.get("Skills", [])

        try:
            match_score = float(match)
        except ValueError:
            st.error("Invalid match score value")
            return

        match_percentage = int(match_score * 100)

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            st.markdown("### Match Score")
            st.progress(match_score)
            st.markdown(f"<h1 style='text-align: center;'>{match_percentage}%</h1>", unsafe_allow_html=True)

        with col2:
            st.markdown("### Missing Skills")
            if missing_skills:
                for skill in missing_skills:
                    st.markdown(f"- {skill}")
            else:
                st.success("Your resume aligns well with the job description's skills!")

        with col3:
            st.markdown("### Extracted Skills")
            if skills:
                for skill in skills:
                    st.markdown(f"- {skill}")
            else:
                st.warning("No skills found in the resume.")

        # Plot Donut Chart
        # plot_donut_chart(match_score)

    else:
        st.error("Failed to parse the response.")

# Logic for submitting the form
if submit:
    if uploaded_file is not None:
        text = get_pdf_text(uploaded_file)
        response = get_gemini_response(input_prompt_compare.format(text=text, jd=jd))
        response_json = parse_response_compare(response)
        if response_json:
            similarity_score = float(response_json['Match'].strip('"'))
            plot_gauge(similarity_score)
            print("\n")
            st.markdown('---')
            # st.markdown("### Diagramme en secteurs (Donut Chart)")
            plot_donut_chart(similarity_score)
            st.markdown('---')
            format_response_compare(response_json)
    else:
        st.write("Please upload your Resume")
    st.markdown('---')
    st.success("**Pour renforcer votre CV en vue de notre prochaine offre d'emploi, nous vous recommandons de vous concentrer sur les domaines suivants, étroitement liés à nos futures offres d'emploi :**")
    
    # Create an ordered list of recommended courses
    recommended_courses_list = [f"{i+1}. [{course[0]}]({course[1]})" for i, course in enumerate(ds_course)]
    
    # Split the list into groups of six
    grouped_courses = [recommended_courses_list[i:i+6] for i in range(0, len(recommended_courses_list), 6)]
    
    # Display each group of recommended courses
    for group in grouped_courses:
        recommended_courses_str = "\n".join(group)
        st.markdown(recommended_courses_str)
        st.markdown('---')
