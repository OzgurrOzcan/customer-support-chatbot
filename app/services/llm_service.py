"""
LLM Service — OpenAI API calls with AsyncOpenAI client.

Key optimizations:
  1. Uses AsyncOpenAI — native async, no thread overhead
  2. max_tokens=500 — limits output (and cost) per response
  3. Streaming support via SSE for perceived latency reduction
  4. System prompt containing company-specific instructions

The system prompt was ported from the original main.py.
"""

from openai import AsyncOpenAI
from app.core.exceptions import LLMError
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# System prompt — company-specific AI assistant instructions
SYSTEM_PROMPT = """
Sen "Gelişim Pazarlama ve Ticaret" şirketinin resmi AI asistanısın. 
Görevin, sana sağlanan Veri tabanı (Context) içerisindeki verileri kullanarak kullanıcı sorularını yanıtlamaktır.

TALİMATLAR:
1. Sadece sana verilen "Context" içerisindeki bilgileri kullan ancak bilgiler içerisinden kullanıcının sorusuna cevap olabilecek kısımları kullan. Kendi genel bilgilerini veya tahminlerini ASLA cevaba katma.
2. Cevapların profesyonel, nazik ve öz olmalı (Maksimum 8-9 cümle).
3. Eğer "Context" içerisinde kullanıcının sorusuna dair bilgi yoksa, kibarca "Maalesef bu konuyla ilgili güncel verilere sahip değilim." şeklinde cevap ver ve eğer varsa linklerle kullanıcıyı sayfa içerisinde yönlendirmeye çalış. Asla bilgi uydurma.
4. Link Kullanımı: Eğer context içerisinde konuyla ilgili URL'ler varsa, cevabın en altında "Daha Detaylı bilgi için İlgili Bağlantılar:" başlığı aç ve linkleri madde işaretleri (bullet points) halinde ve ALT ALTA şu formatta listele:
   [Linkin Tanımı]: [URL]
   [Linkin Tanımı]: [URL]

   Örnek çıktı formatı:
   Ürün detay linki: https://ornek.com/urun
   İletişim sayfası: https://ornek.com/iletisim
""".strip()


class LLMService:
    """OpenAI LLM service using AsyncOpenAI.

    Uses the native async client to avoid blocking the event loop.
    Connection is pooled and reused across requests.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the async OpenAI client.

        Args:
            api_key: OpenAI API key.
            model: Model to use for completions.
        """
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        logger.info(f"✅ OpenAI AsyncClient initialized (model: {model})")

    async def generate_response(
        self, query: str, context: str
    ) -> str:
        """Generate a response using the OpenAI API.

        Builds the prompt with system instructions + context + query.

        Args:
            query: User's question.
            context: Retrieved Pinecone search results as text.

        Returns:
            The LLM-generated response string.
        """
        try:
            messages = self._build_messages(query, context)

            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=500,
                temperature=0.3,  # Low temperature for factual responses
            )

            answer = response.choices[0].message.content
            logger.info(
                f"LLM response generated | "
                f"tokens_used={response.usage.total_tokens}"
            )
            return answer

        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            raise LLMError(f"OpenAI API call failed: {e}")

    async def generate_stream(
        self, query: str, context: str
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response (SSE) from OpenAI.

        Yields tokens as they arrive, allowing the frontend
        to display responses incrementally.

        Args:
            query: User's question.
            context: Retrieved Pinecone search results as text.

        Yields:
            Individual token strings as they arrive.
        """
        try:
            messages = self._build_messages(query, context)

            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=500,
                temperature=0.3,
                stream=True,
            )

            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            logger.error(f"LLM streaming failed: {e}", exc_info=True)
            raise LLMError(f"OpenAI streaming failed: {e}")

    def _build_messages(self, query: str, context: str) -> list[dict]:
        """Build the prompt message list.

        Args:
            query: User's question.
            context: Formatted context from Pinecone search.

        Returns:
            List of message dicts for the OpenAI API.
        """
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Soru (Query): {query}\n\n"
                    f"Data Base (Context):\n###\n{context}\n###\n\n"
                    f"Yukarıdaki veritabanından gelen veriyi analiz et. "
                    f"Eğer soruyla alakalıysa cevapla ve varsa ilgili "
                    f"linkleri belirtilen formatta sona ekle."
                ),
            },
        ]

    async def close(self) -> None:
        """Close the OpenAI client connection."""
        await self._client.close()
        logger.info("OpenAI client closed")
