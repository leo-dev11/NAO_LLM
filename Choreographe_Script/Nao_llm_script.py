# Este script solo se puede ejecutar dentro del entorno de Choreographe
# Dado que usa Python 2.7 y tiene las librerías que necesita el robot NAO
# NO SE PUEDE EJECUTAR ESTE .py FUERA DEL ENTORNO DEL CHOREOGRAPHE
import json
import ssl
import urllib2
import re
import unicodedata
from naoqi import ALProxy
import time

class MyClass(GeneratedClass):
    def __init__(self):
        GeneratedClass.__init__(self)
        self.vocabulario = ["Who are you?","Lima", "France", "robot", "who are you", "what are you", "what is", "Where is Lima?", "thank you"]
        self.asr = None
        self.memory = None
        self.behavior_mng = None
        self.behavior_name = ".lastUploadedChoregrapheBehavior/thinker"
        self.last_recognition_time = time.time()
        self.recognition_delay = 1.5  # segundos de silencio para considerar "fin de frase"
        self.ultima_palabra = ""

    def onLoad(self):
        pass

    def onUnload(self):
        pass

    def limpiar_texto(self, texto):
        texto = unicodedata.normalize('NFD', texto)
        texto = texto.encode('ascii', 'ignore').decode("utf-8")
        texto = re.sub(r'[\r\n]+', ' ', texto)
        texto = re.sub(r'\s{2,}', ' ', texto)
        return texto.strip()

    def send_to_fastapi(self, prompt):
        #url = "http://192.168.68.1:5000/chat"
        #url = "http://10.11.149.154:5000/chat"
        url = "http://192.168.108.128:5000/chat"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "prompt": prompt
        }

        req = urllib2.Request(url, data=json.dumps(data), headers=headers)
        context = ssl._create_unverified_context()

        try:
            response = urllib2.urlopen(req, context=context)
            res_text = response.read()
            print("Respuesta cruda desde FastAPI:", res_text)
            res_json = json.loads(res_text)
            if 'response' in res_json:
                return res_json['response']
            else:
                return "No se recibió una respuesta válida del servidor."
        except Exception as e:
            return "Error al conectar con la API: " + str(e)

    def escuchar_frase_completa(self):
        import time
        while True:
            if self.ultima_palabra and (time.time() - self.last_recognition_time > self.recognition_delay):
                print("Frase reconocida:", self.ultima_palabra)
                self.procesar_respuesta()
                break
            time.sleep(0.1)

    def onInput_onStart(self):
        #prompt = "Do you know how to code?"
        import threading

        self.asr = ALProxy("ALSpeechRecognition", "127.0.0.1", 9559)
        self.memory = ALProxy("ALMemory", "127.0.0.1", 9559)
        self.behavior_mng = ALProxy("ALBehaviorManager", "127.0.0.1", 9559)

        self.vocabulario = ["Lima", "France", "robot", "who are you", "what are you", "what is", "thank you"]
        self.asr.setLanguage("English")
        self.asr.setVocabulary(self.vocabulario, False)

        self.last_recognition_time = 0
        self.ultima_palabra = ""
        self.memory.subscribeToEvent("WordRecognized", self.getName(), "onWordRecognized")
        self.asr.subscribe("ChatAPI")

        print("Esperando frase completa...")

        # Hilo para esperar fin de frase
        threading.Thread(target=self.escuchar_frase_completa).start()

    def onWordRecognized(self, key, value, msg):
        confidence = value[1]
        palabra = value[0]

        if confidence < 0.4:  # Puedes ajustar esto
            return

        self.ultima_palabra = palabra
        self.last_recognition_time = time.time()  # Actualizar tiempo

    def procesar_respuesta(self):
        try:
            self.memory.unsubscribeToEvent("WordRecognized", self.getName())
            self.asr.unsubscribe("ChatAPI")
        except:
            pass

        try:
            if not self.behavior_mng.isBehaviorRunning(self.behavior_name):
                self.behavior_mng.startBehavior(self.behavior_name)
        except Exception as e:
            print("Error al iniciar comportamiento:", str(e))

        respuesta = self.send_to_fastapi(self.ultima_palabra)
        texto_limpio = self.limpiar_texto(respuesta)

        print("Texto limpio que dirá el robot:", texto_limpio)

        try:
            if self.behavior_mng.isBehaviorRunning(self.behavior_name):
                self.behavior_mng.stopBehavior(self.behavior_name)
        except Exception as e:
            print("Error al detener comportamiento:", str(e))

        try:
            tts = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)
            if texto_limpio:
                tts.say(str(texto_limpio.encode("utf-8")))
            else:
                tts.say("I did not understand.")
        except Exception as e:
            print("Error al hablar:", str(e))

        self.onStopped()
    def onInput_onStop(self):
        try:
            self.memory.unsubscribeToEvent("WordRecognized",self.getName(),"onWordRecognized")
            self.asr.unsubscribe("ChatAPI")
        except:
            pass
        self.onStopped()