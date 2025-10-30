from datetime import datetime
from app.callout.autowrite.router import Router
from app.models.schemas import AutoWriteRequest, AutoWriteResponse
from app.processors.autowrite_postprocessing import safe_strip, clamp_length


class AutoWriteService:
    """AI 호출 및 실패시 정형화된 출력문 출력"""

    async def generate_intro(self, req: AutoWriteRequest) -> AutoWriteRequest:
        router = Router()
        provider = router.get_provider()

        try:
            result = await provider.generate_intro(req.dict())
        except Exception:
            result = self.render_meeting_template_friendly_extra_long(req)

        cleaned = safe_strip(result)
        limited = clamp_length(cleaned, max_chars=req.max_chars)

        return AutoWriteResponse(
            room_id=req.room_id,
            description=limited,
            actual_length=len(limited),
            gender_neutral_applied=req.gender_neutral,
            used_model=provider.model if "failed" not in limited else "fallback-template",
            prompt_version="intro_gen_v1"
        )

    def render_meeting_template_friendly_extra_long(self, dto: AutoWriteRequest) -> str:
        date = (
            datetime.fromisoformat(dto.date_time).strftime("%Y년 %m월 %d일이고,")
            if dto.date_time
            else "미정"
        )

        intro = f"🌟 안녕하세요! 『{dto.title}』 모임에 관심 가져주셔서 정말 반가워요! 🌟\n"

        part1 = (
            f"이번 모임은 {dto.category}에 흥미가 있거나 관련 경험을 나누고 싶은 분들을 위해 준비한 자리예요. "
            f"📌 일시는 {date}, 📍 장소는 {dto.location}입니다. "
            "바쁜 일정 속에서도 잠시 시간을 내어 함께한다면, 분명 새로운 에너지와 즐거움을 얻으실 수 있을 거예요. ✨"
        )

        part2 = (
            f"정원은 {dto.max_participants}명으로 제한되어 있습니다!. 😊 "
        )
        if dto.gender_neutral:
            part2 += "성별이나 배경에 상관없이 누구나 환영하고 있으니, 부담 없이 오시면 됩니다."

        part3 = (
            "처음 참여하시는 분들도 걱정하지 않으셔도 돼요. 사실 대부분의 참가자분들이 "
            "‘낯설지 않을까?’, ‘내가 잘 어울릴 수 있을까?’라는 생각을 하시지만, 막상 오시면 "
            "누구보다도 금방 어울리고 즐겁게 시간을 보내시더라구요. 😉 "
            "우리 모임의 분위기는 언제나 따뜻하고 열린 마음을 가진 분들 덕분에 금세 편안해집니다."
        )

        part3 = (
            "『{title}』 모임은 함께 웃고 공감하며 "
            "서로의 일상 이야기도 나눌 수 있는 특별한 공간이 되었으면 합니다. "
            "때로는 새로운 아이디어를 얻기도 하고, 때로는 그냥 편하게 대화하다가 스트레스를 풀기도 하죠. "
            "아마 오셔서 앉아 계시다 보면 ‘아, 오길 잘했다’라는 생각을 자연스럽게 하실 거예요. 💡"
        ).format(title=dto.title)

        part4 = (
            "혹시 아직도 고민하고 계신가요? 그렇다면 이렇게 생각해 보세요. "
            "이번 기회를 놓치면 또 언제 이런 자리를 만나게 될까요? 🕒 "
            "우리 삶은 늘 바쁘고 해야 할 일들은 끝이 없지만, 그 속에서도 잠시 멈춰서 "
            "새로운 사람들과 연결되는 경험은 오래도록 남습니다. "
            f"정원 {dto.max_participants}명이라 금방 마감될 수 있으니, 지금 바로 신청하시는 걸 추천드려요! 🚀"
        )

        closing = (
            "마지막으로, 여러분을 따뜻하게 맞이할 준비는 이미 다 되어 있습니다. "
            "누구보다도 반가운 마음으로 기다리고 있을게요. 🥳 "
            "이번 『{title}』 모임에서 꼭 뵐 수 있기를 바랍니다. "
            "그날 함께 웃고, 배우고, 또 좋은 인연을 만들어가요! 🙏"
        ).format(title=dto.title)

        return "\n\n".join([intro, part1, part2, part3, part4, closing])
        
