
import csv
import os
import statistics

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp

ARQUIVO = "medicoes_pilha.csv"


class Grafico(Widget):
    def __init__(self, dados, **kwargs):
        super().__init__(**kwargs)
        self.dados = sorted(dados, key=lambda d: d["tempo"])
        self.bind(size=self.desenhar, pos=self.desenhar)
        self.desenhar()

    def desenhar(self, *args):
        self.canvas.clear()

        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)

            if not self.dados:
                return

            margem_esq = dp(45)
            margem_dir = dp(15)
            margem_inf = dp(35)
            margem_sup = dp(20)

            x0 = self.x + margem_esq
            y0 = self.y + margem_inf
            largura = max(dp(10), self.width - margem_esq - margem_dir)
            altura = max(dp(10), self.height - margem_inf - margem_sup)

            tempos = [d["tempo"] for d in self.dados]
            tensoes = [d["tensao"] for d in self.dados]

            tmin, tmax = min(tempos), max(tempos)
            vmin, vmax = min(tensoes), max(tensoes)

            if tmin == tmax:
                tmin -= 0.5
                tmax += 0.5

            if vmin == vmax:
                vmin = max(0, vmin - 0.5)
                vmax += 0.5

            # Grade
            Color(0.85, 0.85, 0.85, 1)
            for n in range(6):
                y = y0 + altura * n / 5
                Line(points=[x0, y, x0 + largura, y], width=1)

            # Eixos
            Color(0.1, 0.1, 0.1, 1)
            Line(points=[
                x0, y0, x0, y0 + altura
            ], width=1.5)
            Line(points=[
                x0, y0, x0 + largura, y0
            ], width=1.5)

            # Linha e pontos das medições
            pontos = []
            for t, v in zip(tempos, tensoes):
                x = x0 + (t - tmin) / (tmax - tmin) * largura
                y = y0 + (v - vmin) / (vmax - vmin) * altura
                pontos.extend([x, y])

            Color(0.05, 0.45, 0.8, 1)

            if len(pontos) >= 4:
                Line(points=pontos, width=dp(2))

            for i in range(0, len(pontos), 2):
                Ellipse(
                    pos=(
                        pontos[i] - dp(4),
                        pontos[i + 1] - dp(4)
                    ),
                    size=(dp(8), dp(8))
                )

        # Os valores dos eixos são mostrados nos rótulos
        # da janela do gráfico.


class MonitorPilha(App):
    def build(self):
        self.dados = []
        self.carregar()

        Window.clearcolor = (0.08, 0.10, 0.14, 1)

        raiz = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        raiz.add_widget(Label(
            text="MONITOR DE PILHA CASEIRA",
            font_size="22sp",
            size_hint_y=None,
            height=dp(55)
        ))

        rolagem = ScrollView()
        conteudo = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None
        )
        conteudo.bind(
            minimum_height=conteudo.setter("height")
        )

        self.tempo = self.campo("Tempo (min)")
        self.tensao = self.campo("Tensão (V)")
        self.corrente = self.campo("Corrente (mA, opcional)")

        for campo in (
            self.tempo, self.tensao, self.corrente
        ):
            conteudo.add_widget(campo)

        self.botao(
            conteudo, "Registrar medição", self.registrar
        )
        self.botao(
            conteudo, "Ver estatísticas", self.estatisticas
        )
        self.botao(
            conteudo, "Ver gráfico", self.ver_grafico
        )
        self.botao(
            conteudo, "Exportar relatório", self.relatorio
        )
        self.botao(
            conteudo, "Limpar resultado", self.limpar
        )

        self.resultado = Label(
            text="Pronto para registrar medições.",
            size_hint_y=None,
            height=dp(180),
            halign="left",
            valign="top"
        )
        self.resultado.bind(
            size=lambda obj, size:
            setattr(obj, "text_size", size)
        )
        conteudo.add_widget(self.resultado)

        rolagem.add_widget(conteudo)
        raiz.add_widget(rolagem)
        return raiz

    def campo(self, dica):
        return TextInput(
            hint_text=dica,
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=dp(50),
            font_size="18sp"
        )

    def botao(self, local, texto, funcao):
        b = Button(
            text=texto,
            size_hint_y=None,
            height=dp(52),
            font_size="17sp"
        )
        b.bind(on_release=funcao)
        local.add_widget(b)

    def carregar(self):
        if not os.path.exists(ARQUIVO):
            return

        try:
            with open(
                ARQUIVO, newline="", encoding="utf-8"
            ) as f:
                for linha in csv.DictReader(f):
                    self.dados.append({
                        "tempo": float(linha["tempo_min"]),
                        "tensao": float(linha["tensao_V"]),
                        "corrente": (
                            float(linha["corrente_mA"])
                            if linha["corrente_mA"] else None
                        )
                    })
        except (ValueError, KeyError, OSError):
            self.dados = []

    def salvar(self):
        with open(
            ARQUIVO, "w", newline="", encoding="utf-8"
        ) as f:
            campos = [
                "tempo_min", "tensao_V", "corrente_mA"
            ]
            escritor = csv.DictWriter(
                f, fieldnames=campos
            )
            escritor.writeheader()

            for d in self.dados:
                escritor.writerow({
                    "tempo_min": d["tempo"],
                    "tensao_V": d["tensao"],
                    "corrente_mA": (
                        "" if d["corrente"] is None
                        else d["corrente"]
                    )
                })

    def registrar(self, *_):
        try:
            tempo = float(self.tempo.text.replace(",", "."))
            tensao = float(self.tensao.text.replace(",", "."))
            corrente = (
                float(self.corrente.text.replace(",", "."))
                if self.corrente.text.strip() else None
            )

            if tempo < 0 or tensao < 0:
                raise ValueError
            if corrente is not None and corrente < 0:
                raise ValueError

            self.dados.append({
                "tempo": tempo,
                "tensao": tensao,
                "corrente": corrente
            })
            self.salvar()

            self.tempo.text = ""
            self.tensao.text = ""
            self.corrente.text = ""

            self.resultado.text = (
                f"Medição salva!\n"
                f"Tempo: {tempo:.2f} min\n"
                f"Tensão: {tensao:.3f} V\n"
                f"Total: {len(self.dados)} medições"
            )

        except ValueError:
            self.resultado.text = (
                "Confira os campos e digite números válidos."
            )
        except OSError as erro:
            self.resultado.text = f"Erro ao salvar: {erro}"

    def estatisticas(self, *_):
        if not self.dados:
            self.resultado.text = "Nenhuma medição registrada."
            return

        v = [d["tensao"] for d in self.dados]
        linhas = [
            f"Total: {len(v)}",
            f"Tensão média: {statistics.mean(v):.3f} V",
            f"Tensão máxima: {max(v):.3f} V",
            f"Tensão mínima: {min(v):.3f} V"
        ]

        if len(v) > 1:
            linhas.append(
                f"Desvio padrão: {statistics.stdev(v):.3f} V"
            )

        if len(v) > 1 and v[0] != 0:
            variacao = (v[-1] - v[0]) / v[0] * 100
            linhas.append(f"Variação: {variacao:.1f}%")

        correntes = [
            d for d in self.dados
            if d["corrente"] is not None
            and d["corrente"] > 0
        ]

        if correntes:
            potencias = [
                d["tensao"] * d["corrente"]
                for d in correntes
            ]
            linhas.append(
                f"Potência média: "
                f"{statistics.mean(potencias):.3f} mW"
            )

        self.resultado.text = "\n".join(linhas)

    def ver_grafico(self, *_):
        if not self.dados:
            self.resultado.text = "Registre uma medição primeiro."
            return

        layout = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(5)
        )

        layout.add_widget(Label(
            text="Tensão (V) por tempo (min)",
            size_hint_y=None,
            height=dp(40),
            color=(0, 0, 0, 1)
        ))

        grafico = Grafico(
            self.dados,
            size_hint=(1, 1)
        )
        layout.add_widget(grafico)

        layout.add_widget(Label(
            text=(
                f"Tempo: {min(d['tempo'] for d in self.dados):g}"
                f" a {max(d['tempo'] for d in self.dados):g} min"
                f" | Tensão: {min(d['tensao'] for d in self.dados):.3f}"
                f" a {max(d['tensao'] for d in self.dados):.3f} V"
            ),
            size_hint_y=None,
            height=dp(45),
            color=(0, 0, 0, 1),
            font_size="12sp"
        ))

        popup = Popup(
            title="Gráfico da pilha",
            content=layout,
            size_hint=(0.95, 0.8)
        )
        popup.open()

    def relatorio(self, *_):
        try:
            with open(
                "relatorio_resultados.txt",
                "w", encoding="utf-8"
            ) as f:
                f.write("RELATÓRIO - PILHA CASEIRA\n\n")
                f.write(f"Total: {len(self.dados)}\n\n")

                for d in sorted(
                    self.dados, key=lambda x: x["tempo"]
                ):
                    f.write(
                        f"Tempo: {d['tempo']:.2f} min | "
                        f"Tensão: {d['tensao']:.3f} V | "
                        f"Corrente: {d['corrente']} mA\n"
                    )

            self.resultado.text = "Relatório exportado!"
        except OSError as erro:
            self.resultado.text = f"Erro: {erro}"

    def limpar(self, *_):
        self.resultado.text = "Resultado limpo. Dados preservados."


if __name__ == "__main__":
    MonitorPilha().run()
