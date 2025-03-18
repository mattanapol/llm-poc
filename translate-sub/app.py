import streamlit as st
from io import StringIO
import os
import ai_translate

def get_original_text_from_file(file_obj):
    str_io = StringIO(file_obj.getvalue().decode("utf-8"))

    events_section = False
    text_column = []

    for line in str_io:
        if line.strip() == '[Events]':
            events_section = True
            continue
        if events_section and line.startswith('Dialogue'):
            text = line.split(',', maxsplit=9)[-1].strip()
            text_column.append(text)
    return text_column

def get_output_filename(filename):
  base, ext = os.path.splitext(filename)
  return f"{base}_translated{ext}"

def save_translated(file_obj, translated_list: list):
    str_io = StringIO(file_obj.getvalue().decode("utf-8"))

    events_section = False
    translated_index = 0
    updated_lines = []

    for line in str_io:
        if line.strip() == '[Events]':
            events_section = True
            updated_lines.append(line)
            continue
        if events_section and line.startswith('Dialogue'):
            parts = line.split(',', maxsplit=9)
            if translated_index < len(translated_list) and len(translated_list[translated_index]) > 0:
                parts[-1] = translated_list[translated_index] + "\n"
            translated_index += 1
            updated_line = ','.join(parts)
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)

    output = StringIO()
    output.writelines(updated_lines)
    output.seek(0)
    return output.getvalue().encode("utf-8")

def get_glossary_dict(file_obj):
    str_io = StringIO(file_obj.getvalue().decode("utf-8"))
    glossary_dict = {}
    for line in str_io:
        try:
            key, value = line.split("\t")
        except ValueError:
            continue
        glossary_dict[key] = value
    return glossary_dict

def main():
    st.title("Translation App")
    translations = []
    # Input file selection
    st.sidebar.write("Original File")
    original_file = st.sidebar.file_uploader("Choose a file:")

    if original_file is not None:
        original_lines = get_original_text_from_file(original_file)

        # AI Translation button
        st.sidebar.write("AI Translation")
        glossary_dict = {}
        glossary_file = st.sidebar.file_uploader("Choose a glossary file:")
        if glossary_file is not None:
            glossary_dict = get_glossary_dict(glossary_file)
        if st.sidebar.button("Generate AI Translation"):
            translated_text = ai_translate.translate(original_lines, glossary_dict)
            for key, value in translated_text.items():
                if len(value) > 0:
                    st.session_state["input" + str(key)] = value
            st.sidebar.success("AI Translation generated successfully!")

        index = 0
        for original_line in original_lines:
            translated_text = st.text_input(original_line.strip(), key="input" + str(index), value="")
            translations.append(translated_text)
            index += 1

        # Save button
        st.sidebar.write("Save Translations")
        if st.sidebar.button("Generate Translation"):
            st.sidebar.success("Translation generated successfully!")
            st.sidebar.download_button("Save Translations", save_translated(original_file, translations), get_output_filename(original_file.name))

if __name__ == '__main__':
    main()