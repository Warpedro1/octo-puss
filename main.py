import openai
from dotenv import load_dotenv
import os
import requests
from pydub import AudioSegment

def carrega(caminho, modo):
    try: 
        with open(caminho, modo) as arquivo:
            return arquivo.read()

    except IOError as e:
        print(f"Erro {e} ao abrir {caminho}")

def salva(nome_arquivo, conteudo):
    try:
        with open(nome_arquivo,"w",encoding='utf-8') as arquivo:
            arquivo.write(conteudo)

    except IOError as e:
        print(f"Erro {e} ao tentar salvar o arquivo {arquivo}")

def openai_whisper(caminho, nome_arquivo, modelo, client):
    print("Iniciando tanscricao com whispers . . .")

    audio = open(caminho,"rb")

    resposta = client.audio.transcriptions.create(
        model = modelo,
        file = audio,
        #response_format="text"
    )
    
    transcricao = resposta.text

    """ traducao = client.audio.translations.create(
        model=modelo,
        file=audio
    )
    salva(f"traducao_{nome_arquivo}.txt" ,traducao.text) """

    salva(f"resposta_{nome_arquivo}.txt" ,transcricao)
    
    return transcricao

def resumir( conteudo, nome_arquivo, client):
    print("Resumindo com o gpt . . .")

    prompt_sistema = """
    Assuma que voce é um influencer que esta construindo conteudo das areas de autoconhecimentoem uma plataforma de audio(podcast).

    Os textos produzidos devem levar em consideracao uma persona que consumira os conteudos gerados. Leve em consideracao: 

    - Seus seguidores são pessoas que querem melhorar suas mentalidades, que amam consumir conteúdos relacionados aos principais temas de desenvolvimento pessoal.
    - Você deve ser assertivo em seus textos.
    - Os textos serão utilizados para fazer os ouvintes refletirem sobre seu estilo de vida
    - O texto deve ser escrito em português do Brasil.
    """

    prompt_usuario = """
        . \nReescreva a transcrição acima para que possa ser postado como uma legenda do Instagram. Ela deve resumir o texto para chamada na rede social. Inclua hashtags
    """
    messages = [
        {
            "role" : "system",
            "content" : prompt_sistema
        },
        {
            "role" : "user",
            "content" : conteudo + prompt_usuario
        }
    ]

    resposta = chat(messages, client,"gpt-3.5-turbo-16k", temperature=0.6 )  #"gpt-3.5-turbo-16k"pode consumir ate 16mil tokens de acesso

    resumo_instagram = resposta

    salva(f"resposta_insta.txt",resumo_instagram)

    return resumo_instagram

def criar_hashtag(resumo, arquivo, client):
    print("CRIANDO HASHTAGS . . .")

    prompt_sistema= """
    Assuma que você é um digital influencer digital e que está construíndo conteúdos das áreas de autoconhecimento em uma plataforma de áudio (podcast).

    Os textos produzidos devem levar em consideração uma persona que consumirá os conteúdos gerados. Leve em consideração:

    - Seus seguidores são pessoas super conectadas da autoconhecimento, que amam consumir conteúdos relacionados aos principais temas da desenvolvimento pessoal.
    - Você deve usar uma comunicacao clara e assertiva.
    - Os textos serão utilizados para fazer as pessoas refletirem sobre si mesmas e suas vidas
    - O texto deve ser escrito em português do Brasil.
    - A saída deve conter 5 hashtags.
    """
    prompt_usuario = f'Aqui está um resumo de um texto "{resumo}". Por favor, gere 5 hashtags que sejam relevantes para este texto e que possam ser publicadas no Instagram.  Por favor, faça isso em português do Brasil '

    messages = [
        {
            "role":"system",
            "content":prompt_sistema
        },
        {
            "role":"user",
            "content":prompt_usuario
        }
    ]

    resposta = chat(messages,client, "gpt-3.5-turbo")
    salva(f"respota_hashtags.txt",resposta)
    return resposta
    
def chat(messages, client, modelo, temperature = None):
    try:
        resposta = client.chat.completions.create(
            messages=messages,
            model=modelo,
            temperature = None
        )
        return resposta.choices[0].message.content
    except openai.AuthenticationError as e:
        print(f"Erro de autenticacao {e}")
    except openai.OpenAIError as e:
        print(f"Erro de comunicacao {e}")

def gerar_texto_imagem(resumo, nome_arquivo, client):
    print("GERANDO TEXTO PARA CRIACAO DE IMAGEM . . .")
    
    prompt_sistema="""
    - A saída deve ser uma única, do tamanho de um tweet, que seja capaz de descrever o conteúdo do texto para que possa ser transcrito como uma imagem.
    - Não inclua hashtags
    """

    prompt_usuario = f'Reescreva o texto a seguir, em uma frase, para que descrever o texto abaixo em um tweet: {resumo}'

    messages = [
        {
            "role":"system",
            "content":prompt_sistema
        },
        {
            "role":"user",
            "content":prompt_usuario
        }
    ]

    resposta = chat(messages,client, "gpt-3.5-turbo", temperature=0.6)
    salva(f"respota_texto_imagem.txt",resposta)
    return resposta

def openai_dalle_gerar_imagem(resolucao, resumo_para_imagem, modelo, client, qtd_imagens = 1):
    print("Criando uma imagem utilizando a API do DALL-E ...")

    prompt_user = "Crie uma foto de como se parece a pessoa que falou isso com base em esteriotipos sociais: " + resumo_para_imagem
    
    
    try:
        resposta = client.images.generate(
        prompt =prompt_user,
        n = qtd_imagens,
        size = resolucao,
        model = modelo
    )
        return resposta.data
    except openai.AuthenticationError as e:
        print(f"Erro de autenticacao {e}")
    except openai.OpenAIError as e:
        print(f"Erro de comunicacao {e}")

def download_imagem(nome_arquivo, imagem, qtd_imagens = 1):
    print("comecando download_imagem . . .")
    nome_imagens = []
    try:
        for quantidade in range(0,qtd_imagens):
            caminho = imagem[quantidade].url
            image = requests.get(caminho)
            with open(f"images/{nome_arquivo}_{quantidade}.png","wb") as arquivo:
                arquivo.write(image.content)

            nome_imagens.append(f"{nome_arquivo}_{quantidade}.png")
        return nome_imagens
    except IOError as e:
        print(f"Erro: {e}")

def audio_em_partes(caminho_audio, arquivo):
    print("Iniciando audio em partes . . . ")

    try:
        audio = AudioSegment.from_mp3(caminho_audio)
    except FileNotFoundError as e:
        print(f"Erro not found: {e}")
    except Exception as e:
        print(f"Erro aqui: {e}")

    dez_minutos = 10 * 60 * 1000 # milisegundos
    count_pedaco = 1 
    arquivos_exportados = []

    while len(audio > 0):
        pedaco = audio[:dez_minutos]
        nome_pedaco = f"{arquivo}_parte_{count_pedaco}.mp3"
        pedaco.export(nome_pedaco, format="mp3")
        arquivos_exportados.append(nome_pedaco)
        audio = audio[dez_minutos:]
        count_pedaco+=1

    return arquivos_exportados

def openai_whisper_partes(caminho, nome_arquivo, modelo, client):
    print("Iniciando tanscricao em partes com whispers . . .")

    lista_arquivos_audios = audio_em_partes(caminho,nome_arquivo)
    
    pedacos_audio = []

    for pedaco in lista_arquivos_audios:
   
        audio = open(caminho,"rb")

        resposta = client.audio.transcriptions.create(
            model = modelo,
            file = audio,
            #response_format="text"
        )
        
        transcricao = resposta.text
        pedacos_audio.append(transcricao)

    transcricao = "".join(pedacos_audio)
    """ traducao = client.audio.translations.create(
        model=modelo,
        file=audio
    )
    salva(f"traducao_{nome_arquivo}.txt" ,traducao.text) """

    salva(f"respostas/resposta_{nome_arquivo}.txt" ,transcricao)
    
    return transcricao

def main():
    load_dotenv()
    
    caminho_audio = "podcasts\WATCH_THIS_EVERYDAY_AND_CHANGE_YOUR_LIFE_Denzel_Washington_Motivational_Speech_2023.mp3"
    nome_arquivo = "Motivational_Speech"
    url_video = "https://www.youtube.com/watch?v=tbnzAVRZ9Xc"
    qtd_imagens = 2

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    modelo_whisper ="whisper-1"

    openai_whisper_partes("podcasts/not_enough.mp3", "not_enough", modelo_whisper, client)

    #transcricao_completa = openai_whisper(caminho_audio, nome_arquivo, modelo_whisper, client)
    transcricao_completa = carrega("resposta_WATCH_THIS_EVERYDAY_AND_CHANGE_YOUR_LIFE_Denzel_Washington_Motivational_Speech_2023.txt", "r")
    
    #resumo_instagram = resumir( transcricao_completa, nome_arquivo ,client)
    resumo_instagram = carrega("resposta_insta.txt","r")

    #hashtags = criar_hashtag(resumo_instagram, nome_arquivo, client)
    hashtags = carrega("respota_hashtags.txt","r")
    
    #resumo_texto_imagem = gerar_texto_imagem(resumo_instagram, nome_arquivo, client)
    resumo_texto_imagem = carrega("respota_texto_imagem.txt", "r")

    #url_imagem = openai_dalle_gerar_imagem("1024x1024",resumo_texto_imagem, "dall-e-2", client, qtd_imagens)

    #download_imagem(nome_arquivo, url_imagem, qtd_imagens)

    

if __name__ == "__main__":
    main()