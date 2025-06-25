#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;

int passos = 0;
int sequencia[100][4];
bool rodando = false;
bool resetando = false;
bool manual = false;
bool modo_rodar_uma_vez = false;
int velocidade = 5;

int posicoesAtuais[4] = {90, 90, 90, 90};
int alvoAtual[4] = {90, 90, 90, 90};

const int pino_servo1 = 8;
const int pino_servo2 = 9;
const int pino_servo3 = 10;
const int pino_servo4 = 11;

void setup() {
  Serial.begin(9600);

  servo1.attach(pino_servo1);
  servo2.attach(pino_servo2);
  servo3.attach(pino_servo3);
  servo4.attach(pino_servo4);

  servo1.write(posicoesAtuais[0]);
  servo2.write(posicoesAtuais[1]);
  servo3.write(posicoesAtuais[2]);
  servo4.write(posicoesAtuais[3]);

  Serial.println("Arduino pronto.");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();

    if (c == 'S' || c == 'X') {
      String dados = Serial.readStringUntil('\n');
      parseSequencia(dados);
      rodando = true;
      resetando = false;
      manual = false;
      modo_rodar_uma_vez = (c == 'X'); // Se recebeu X, é para rodar apenas 1x
      Serial.println(modo_rodar_uma_vez ? "Sequência 1x carregada." : "Sequência em loop carregada.");
    }
    else if (c == 'P') {
      rodando = false;
      resetando = false;
      manual = false;
      Serial.println("Parado.");
    }
    else if (c == 'R') {
      rodando = false;
      resetando = true;
      manual = false;
      Serial.println("Reset iniciado.");
    }
    else if (c == 'V') {
      String valor = Serial.readStringUntil('\n');
      int nova_velocidade = valor.toInt();
      if (nova_velocidade >= 1 && nova_velocidade <= 10) {
        velocidade = nova_velocidade;
        Serial.print("Velocidade ajustada para ");
        Serial.println(velocidade);
      }
    }
    else if (c >= '1' && c <= '8') {
      int comando = c - '0'; // Converte char para número
      rodando = false;
      resetando = false;
      manual = true;
      executarMovimentoManual(comando);
    }
    else if (c == 'G') {
      String resposta = String(posicoesAtuais[0]) + "," +
                         String(posicoesAtuais[1]) + "," +
                         String(posicoesAtuais[2]) + "," +
                         String(posicoesAtuais[3]);
      Serial.println(resposta);
    }
  }

  if (rodando) {
    executarSequenciaSuave();
  }
  if (resetando) {
    resetarPara90();
  }
}

void executarMovimentoManual(int cmd) {
  switch (cmd) {
    case 1: posicoesAtuais[0] = constrain(posicoesAtuais[0] + 1, 0, 180); break; // Base Esquerda
    case 2: posicoesAtuais[0] = constrain(posicoesAtuais[0] - 1, 0, 180); break; // Base Direita
    case 3: posicoesAtuais[1] = constrain(posicoesAtuais[1] + 1, 0, 180); break; // Braço Sobe
    case 4: posicoesAtuais[1] = constrain(posicoesAtuais[1] - 1, 0, 180); break; // Braço Desce
    case 5: posicoesAtuais[2] = constrain(posicoesAtuais[2] + 1, 0, 180); break; // Cotovelo Sobe
    case 6: posicoesAtuais[2] = constrain(posicoesAtuais[2] - 1, 0, 180); break; // Cotovelo Desce
    case 7: posicoesAtuais[3] = constrain(posicoesAtuais[3] + 1, 1, 90); break; // Garra Abre
    case 8: posicoesAtuais[3] = constrain(posicoesAtuais[3] - 1, 1, 90); break; // Garra Fecha
  }

  servo1.write(posicoesAtuais[0]);
  servo2.write(posicoesAtuais[1]);
  servo3.write(posicoesAtuais[2]);
  servo4.write(posicoesAtuais[3]);
}

void parseSequencia(String dados) {
  passos = 0;
  while (dados.length() > 0 && passos < 100) {
    int sep = dados.indexOf('|');
    String linha;
    if (sep == -1) {
      linha = dados;
      dados = "";
    } else {
      linha = dados.substring(0, sep);
      dados = dados.substring(sep + 1);
    }

    int p1 = linha.substring(0, linha.indexOf(',')).toInt();
    linha = linha.substring(linha.indexOf(',') + 1);
    int p2 = linha.substring(0, linha.indexOf(',')).toInt();
    linha = linha.substring(linha.indexOf(',') + 1);
    int p3 = linha.substring(0, linha.indexOf(',')).toInt();
    linha = linha.substring(linha.indexOf(',') + 1);
    int p4 = linha.toInt();

    sequencia[passos][0] = p1;
    sequencia[passos][1] = p2;
    sequencia[passos][2] = p3;
    sequencia[passos][3] = p4;
    passos++;
  }
}

void executarSequenciaSuave() {
  static unsigned long lastUpdate = 0;
  static int idx = 0;
  static bool alvoDefinido = false;

  unsigned long agora = millis();
  unsigned long intervalo = map(velocidade, 1, 10, 100, 10);

  if (!alvoDefinido) {
    for (int i = 0; i < 4; i++) {
      alvoAtual[i] = sequencia[idx][i];
    }
    alvoDefinido = true;
  }

  if (agora - lastUpdate >= intervalo) {
    for (int i = 0; i < 4; i++) {
      if (posicoesAtuais[i] < alvoAtual[i]) posicoesAtuais[i]++;
      else if (posicoesAtuais[i] > alvoAtual[i]) posicoesAtuais[i]--;
    }

    servo1.write(posicoesAtuais[0]);
    servo2.write(posicoesAtuais[1]);
    servo3.write(posicoesAtuais[2]);
    servo4.write(posicoesAtuais[3]);

    bool chegou = true;
    for (int i = 0; i < 4; i++) {
      if (posicoesAtuais[i] != alvoAtual[i]) chegou = false;
    }
    if (chegou) {
      idx++;
      if (idx >= passos) {
        if (modo_rodar_uma_vez) {
          rodando = false;
          idx = 0;
          Serial.println("Sequência 1x concluída.");
        } else {
          idx = 0;
        }
      }
      alvoDefinido = false;
    }
    lastUpdate = agora;
  }
}

void resetarPara90() {
  static unsigned long lastReset = 0;
  unsigned long agora = millis();
  unsigned long intervalo = map(velocidade, 1, 10, 100, 10);

  if (agora - lastReset >= intervalo) {
    bool terminou = true;
    for (int i = 0; i < 4; i++) {
      if (posicoesAtuais[i] < 90) {
        posicoesAtuais[i]++;
        terminou = false;
      } else if (posicoesAtuais[i] > 90) {
        posicoesAtuais[i]--;
        terminou = false;
      }
    }
    servo1.write(posicoesAtuais[0]);
    servo2.write(posicoesAtuais[1]);
    servo3.write(posicoesAtuais[2]);
    servo4.write(posicoesAtuais[3]);

    lastReset = agora;

    if (terminou) {
      resetando = false;
      Serial.println("Reset completo.");
    }
  }
}
