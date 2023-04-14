import gradio as gr
import os
import shutil
from chains.local_doc_qa import LocalDocQA
from configs.model_config import *


def get_file_list():
    if not os.path.exists("content"):
        return []
    return [f for f in os.listdir("content")]


file_list = get_file_list()

embedding_model_dict_list = list(embedding_model_dict.keys())

llm_model_dict_list = list(llm_model_dict.keys())

local_doc_qa = LocalDocQA()


def upload_file(file):
    if not os.path.exists("content"):
        os.mkdir("content")
    filename = os.path.basename(file.name)
    shutil.move(file.name, "content/" + filename)
    # file_list首位插入新上传的文件
    file_list.insert(0, filename)
    return gr.Dropdown.update(choices=file_list, value=filename)


def get_answer(query, vs_path, history):
    resp, history = local_doc_qa.get_knowledge_based_answer(
        query=query, vs_path=vs_path, chat_history=history)
    return history, history


def get_model_status(history):
    return history + [[None, "模型已完成加载，请选择要加载的文档"]]


def get_file_status(history):
    return history + [[None, "文档已完成加载，请开始提问"]]


def init_model():
    try:
        local_doc_qa.init_cfg()
        return """模型已成功加载，请选择文件后点击"加载文件"按钮"""
    except:
        return """模型未成功加载，请重新选择后点击"加载模型"按钮"""


def reinit_model(llm_model, embedding_model, llm_history_len, top_k):
    local_doc_qa.init_cfg(llm_model=llm_model,
                          embedding_model=embedding_model,
                          llm_history_len=llm_history_len,
                          top_k=top_k),


def get_vector_store(filepath):
    local_doc_qa.init_knowledge_vector_store("content/"+filepath)


model_status = gr.State()
history = gr.State([])
vs_path = gr.State()
model_status = init_model()
with gr.Blocks(css="""
.importantButton {
    background: linear-gradient(45deg, #7e0570,#5d1c99, #6e00ff) !important;
    border: none !important;
}

.importantButton:hover {
    background: linear-gradient(45deg, #ff00e0,#8500ff, #6e00ff) !important;
    border: none !important;
}

""") as demo:
    gr.Markdown(
        f"""
# 🎉langchain-ChatGLM WebUI🎉

👍 [https://github.com/imClumsyPanda/langchain-ChatGLM](https://github.com/imClumsyPanda/langchain-ChatGLM)

""")
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot([[None, """欢迎使用 langchain-ChatGLM Web UI，开始提问前，请依次如下 3 个步骤：
1. 选择语言模型、Embedding 模型及相关参数后点击"重新加载模型"，并等待加载完成提示
2. 上传或选择已有文件作为本地知识文档输入后点击"重新加载文档"，并等待加载完成提示
3. 输入要提交的问题后，点击回车提交 """], [None, str(model_status)]],
                                 elem_id="chat-box",
                                 show_label=False).style(height=600)
            query = gr.Textbox(show_label=False,
                               placeholder="请提问",
                               lines=1,
                               value="用200字总结一下"
                               ).style(container=False)

        with gr.Column(scale=1):
            llm_model = gr.Radio(llm_model_dict_list,
                                 label="LLM 模型",
                                 value="chatglm-6b",
                                 interactive=True)
            llm_history_len = gr.Slider(0,
                                        10,
                                        value=3,
                                        step=1,
                                        label="LLM history len",
                                        interactive=True)
            embedding_model = gr.Radio(embedding_model_dict_list,
                                       label="Embedding 模型",
                                       value="text2vec",
                                       interactive=True)
            top_k = gr.Slider(1,
                              20,
                              value=6,
                              step=1,
                              label="向量匹配 top k",
                              interactive=True)
            load_model_button = gr.Button("重新加载模型")

            # with gr.Column():
            with gr.Tab("select"):
                selectFile = gr.Dropdown(file_list,
                                         label="content file",
                                         interactive=True,
                                         value=file_list[0] if len(file_list) > 0 else None)
            with gr.Tab("upload"):
                file = gr.File(label="content file",
                               file_types=['.txt', '.md', '.docx', '.pdf']
                               )  # .style(height=100)
            load_button = gr.Button("重新加载文件")
    load_model_button.click(reinit_model,
                            show_progress=True,
                            api_name="init_cfg",
                            inputs=[llm_model, embedding_model, llm_history_len, top_k]
                            ).then(
        get_model_status, chatbot, chatbot
    )
    # 将上传的文件保存到content文件夹下,并更新下拉框
    file.upload(upload_file,
                inputs=file,
                outputs=selectFile)
    load_button.click(get_vector_store,
                      show_progress=True,
                      api_name="init_knowledge_vector_store",
                      inputs=selectFile,
                      outputs=vs_path
                      )#.then(
    #     get_file_status,
    #     chatbot,
    #     chatbot,
    #     show_progress=True,
    # )
    # query.submit(get_answer,
    #              [query, vs_path, chatbot],
    #              [chatbot, history],
    #              api_name="get_knowledge_based_answer"
    #              )

demo.queue(concurrency_count=3).launch(
    server_name='0.0.0.0', share=False, inbrowser=False)
