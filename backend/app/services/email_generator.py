"""Groq-based cold email and follow-up generator."""

import re
from typing import Any, Dict, List, Tuple

from app.config import settings
from app.services.llm_provider import groq_provider
from app.utils.json_utils import extract_json_object


class EmailGeneratorService:
    """Generate personalized outreach content using Groq Qwen model only."""

    def _safe_str(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip())

    def _extract_lead_score(self, lead: Dict[str, Any]) -> int:
        raw = lead.get("raw_data") if isinstance(lead.get("raw_data"), dict) else {}
        score = lead.get("total_score")
        if score is None:
            score = raw.get("final_score_100")
        if score is None:
            normalized = raw.get("final_score")
            try:
                score = int(float(normalized) * 100.0)
            except Exception:
                score = 0
        try:
            return max(0, min(100, int(score)))
        except Exception:
            return 0

    def _context_quality(self, lead: Dict[str, Any], company_profile: Dict[str, Any]) -> int:
        decision = lead.get("contact") if isinstance(lead.get("contact"), dict) else {}
        tech_stack = lead.get("tech_stack") if isinstance(lead.get("tech_stack"), (dict, list, str)) else {}

        points = 0
        if self._safe_str(lead.get("company_name") or lead.get("company")):
            points += 1
        if self._safe_str(lead.get("industry")):
            points += 1
        if self._safe_str(lead.get("intent_signal")):
            points += 2
        if self._safe_str(decision.get("name")):
            points += 1
        if self._safe_str(decision.get("title")):
            points += 1
        if self._safe_str(decision.get("email")):
            points += 1
        if tech_stack:
            points += 1
        if company_profile.get("services"):
            points += 1
        if company_profile.get("technologies"):
            points += 1

        # Map context richness to 1-10.
        return max(1, min(10, points))

    def _to_company_profile(self, company_profile: Any) -> Dict[str, Any]:
        if isinstance(company_profile, dict):
            return company_profile

        return {
            "name": self._safe_str(getattr(company_profile, "company_name", "")),
            "services": getattr(company_profile, "services", []) or [],
            "technologies": getattr(company_profile, "technologies", []) or [],
            "industries": getattr(company_profile, "target_industries", []) or [],
            "portfolio_summary": self._safe_str(getattr(company_profile, "company_narrative", "")),
        }

    def _to_lead_payload(self, lead: Any) -> Dict[str, Any]:
        if isinstance(lead, dict):
            payload = dict(lead)
        else:
            raw = getattr(lead, "raw_data", {}) or {}
            enriched = getattr(lead, "enriched_data", {}) or {}
            payload = {
                "company_name": self._safe_str(getattr(lead, "company", "")),
                "industry": self._safe_str(getattr(lead, "industry", "")),
                "location": self._safe_str(raw.get("detected_location") or raw.get("location") or ""),
                "intent_signal": self._safe_str(raw.get("intent_signal") or ""),
                "contact": enriched.get("decision_maker", {}),
                "tech_stack": enriched.get("tech_stack", {}),
                "raw_data": raw,
            }

        payload.setdefault("company_name", self._safe_str(payload.get("company") or payload.get("name") or ""))
        payload.setdefault("intent_signal", self._safe_str(payload.get("intent_signal") or ""))
        payload.setdefault("industry", self._safe_str(payload.get("industry") or ""))
        payload.setdefault("location", self._safe_str(payload.get("location") or ""))
        payload.setdefault("contact", payload.get("decision_maker") if isinstance(payload.get("decision_maker"), dict) else {})
        payload.setdefault("tech_stack", payload.get("tech_stack") or {})
        payload.setdefault("raw_data", payload.get("raw_data") if isinstance(payload.get("raw_data"), dict) else {})
        return payload

    def _truncate_words(self, text: str, max_words: int) -> str:
        words = self._safe_str(text).split()
        if len(words) <= max_words:
            return " ".join(words)
        return " ".join(words[:max_words]).strip()

    def _enforce_email_constraints(self, email_payload: Dict[str, Any], intent_signal: str, context_score: int) -> Dict[str, Any]:
        subject = self._safe_str(email_payload.get("subject", ""))
        body = self._safe_str(email_payload.get("body", ""))

        if not subject:
            subject = "Quick idea for your team"
        if len(subject) >= 50:
            subject = subject[:49].rstrip()

        if not body:
            body = (
                f"Noticed {intent_signal or 'your recent growth momentum'}. "
                "We help teams ship faster with lower delivery risk. "
                "Happy to share one relevant case study and see if this is useful. "
                "Would a 15-minute call next week be worth exploring?"
            )

        intent_hint = self._safe_str(intent_signal)
        if intent_hint:
            first_sentence = body.split(".", 1)[0].lower()
            required_tokens = [t for t in re.split(r"\W+", intent_hint.lower()) if len(t) > 3][:3]
            if required_tokens and not any(token in first_sentence for token in required_tokens):
                body = f"Noticed {intent_hint}. {body}"

        body = self._truncate_words(body, 150)

        try:
            personalization_score = int(email_payload.get("personalization_score", context_score))
        except Exception:
            personalization_score = context_score

        personalization_score = max(1, min(10, personalization_score))
        return {
            "subject": subject,
            "body": body,
            "personalization_score": personalization_score,
        }

    async def _call_groq_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        if not groq_provider.client or not settings.GROQ_API_KEY:
            return {}

        try:
            raw = await groq_provider.call_chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.25,
                max_tokens=520,
                require_json=True,
            )
            parsed = extract_json_object(raw)
            return parsed or {}
        except Exception as e:
            print(f"[EMAIL GEN] Groq generation failed: {e}")
            return {}

    async def generate_cold_email(self, lead: Any, company_profile: Any) -> Dict[str, Any]:
        """Generate hyper-personalized cold email JSON for leads (prioritized for score >= 60)."""
        profile = self._to_company_profile(company_profile)
        lead_payload = self._to_lead_payload(lead)

        lead_score = self._extract_lead_score(lead_payload)
        context_score = self._context_quality(lead_payload, profile)

        intent_signal = self._safe_str(lead_payload.get("intent_signal") or "active demand signal")
        contact = lead_payload.get("contact") if isinstance(lead_payload.get("contact"), dict) else {}

        system_prompt = (
            "You are a B2B outreach specialist. "
            "Return only valid JSON with keys subject, body, personalization_score. "
            "Subject must be under 50 chars. Body must be under 150 words."
        )

        user_prompt = f"""
You are writing a cold outreach email on behalf of {profile.get('name') or 'our company'}.
OUR COMPANY:
- Services: {profile.get('services') or []}
- Key technologies: {profile.get('technologies') or []}
- Industries served: {profile.get('industries') or []}
- Notable portfolio: {profile.get('portfolio_summary') or 'N/A'}
TARGET LEAD:
- Company: {lead_payload.get('company_name')}
- Industry: {lead_payload.get('industry')} / Location: {lead_payload.get('location')}
- Intent signal: {intent_signal}
- Decision maker: {contact.get('name', '')}, {contact.get('title', '')}
- Tech stack: {lead_payload.get('tech_stack')}
Write a cold email that:
1. Subject: specific, curiosity-driven, under 50 chars, no clickbait
2. Opening: 1 sentence referencing their specific intent signal
3. Value prop: 2 sentences max, focused on their industry + tech
4. Social proof: 1 sentence with relevant portfolio reference
5. CTA: single low-friction ask (15-min call or reply with interest)
6. Tone: professional but conversational, not salesy
7. Total: under 150 words
Return JSON: {{"subject": str, "body": str, "personalization_score": int}}
""".strip()

        generated = await self._call_groq_json(system_prompt=system_prompt, user_prompt=user_prompt)
        email_json = self._enforce_email_constraints(generated, intent_signal, context_score)

        # For low-score leads, cap personalization rating to avoid false confidence.
        if lead_score < 60:
            email_json["personalization_score"] = min(email_json["personalization_score"], 5)
        elif lead_score >= 60 and context_score >= 7:
            email_json["personalization_score"] = max(email_json["personalization_score"], 7)

        return email_json

    async def generate_followup_email(
        self,
        lead: Any,
        previous_email: str,
        days_since: int,
        company_profile: Any = None,
    ) -> Dict[str, Any]:
        """Generate day 3/7/14 follow-up email variants with increasing value."""
        profile = self._to_company_profile(company_profile or {})
        lead_payload = self._to_lead_payload(lead)
        intent_signal = self._safe_str(lead_payload.get("intent_signal") or "your current initiative")
        context_score = self._context_quality(lead_payload, profile)

        stage_hint = ""
        if days_since <= 3:
            stage_hint = "day 3 followup: brief reference to first email, add one new insight."
        elif days_since <= 7:
            stage_hint = "day 7 followup: share a concise case study relevant to their industry."
        else:
            stage_hint = "day 14 final followup: final soft ask and offer something concrete."

        system_prompt = (
            "You write concise professional follow-up emails. "
            "Return JSON only with subject, body, personalization_score."
        )
        user_prompt = f"""
Generate a follow-up email for a B2B lead.
Lead company: {lead_payload.get('company_name')}
Lead industry/location: {lead_payload.get('industry')} / {lead_payload.get('location')}
Intent signal: {intent_signal}
Original email: {self._safe_str(previous_email)[:700]}
Stage instruction: {stage_hint}
Rules:
- Subject < 50 chars
- Body < 120 words
- Professional, conversational tone
- Include one low-friction CTA
Return JSON: {{"subject": str, "body": str, "personalization_score": int}}
""".strip()

        generated = await self._call_groq_json(system_prompt=system_prompt, user_prompt=user_prompt)
        followup = self._enforce_email_constraints(generated, intent_signal, context_score)
        followup["body"] = self._truncate_words(followup["body"], 120)

        body_lower = followup["body"].lower()
        if days_since >= 14 and not any(token in body_lower for token in ["case study", "offer", "audit", "free", "assessment"]):
            followup["body"] = self._truncate_words(
                f"{followup['body']} I can also share a relevant case study or a short no-cost assessment if helpful.",
                120,
            )

        return followup

    async def generate_linkedin_message(self, lead: Any, company_profile: Any) -> str:
        """Generate concise LinkedIn connection message (<= 300 chars)."""
        profile = self._to_company_profile(company_profile)
        lead_payload = self._to_lead_payload(lead)

        system_prompt = (
            "You write short high-context LinkedIn messages. "
            "Return JSON only: {\"message\": str}."
        )
        user_prompt = f"""
Write a LinkedIn outreach message under 300 characters.
Sender company: {profile.get('name') or 'our company'}
Services: {profile.get('services') or []}
Lead company: {lead_payload.get('company_name')}
Industry/location: {lead_payload.get('industry')} / {lead_payload.get('location')}
Intent signal: {lead_payload.get('intent_signal')}
Rules:
- Mention one specific signal
- Professional and conversational
- No hard sell
Return JSON: {{"message": str}}
""".strip()

        generated = await self._call_groq_json(system_prompt=system_prompt, user_prompt=user_prompt)
        message = self._safe_str(generated.get("message", ""))
        if not message:
            message = (
                f"Hi, noticed {self._safe_str(lead_payload.get('intent_signal') or 'your current growth initiatives')} "
                f"at {self._safe_str(lead_payload.get('company_name') or 'your team')}. "
                "Would love to share one quick idea if useful."
            )

        if len(message) > 300:
            message = message[:300].rstrip()

        return message


email_generator_service = EmailGeneratorService()
