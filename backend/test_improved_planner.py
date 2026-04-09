import asyncio
from app.services.ai_service import ai_service

async def test_improved_planner():
    result = await ai_service.plan_lead_discovery_queries(
        user_query='find mature e-commerce clients needing web development in mohali',
        filters={'location': 'mohali', 'industry': 'e-commerce', 'services': ['web development']},
        company_profile={'services': ['web development'], 'technologies': ['React', 'Node.js'], 'target_locations': ['Mohali'], 'target_industries': ['e-commerce']},
        retrieved_context=['scaling hiring growth stage series a migration funding'],
        max_queries=10
    )
    
    print("\n" + "="*80)
    print("QUALITY SCORES AFTER IMPROVEMENTS:")
    print("="*80)
    
    for i, q in enumerate(result['queries'], 1):
        print(f"Query {i}: {q}")
    
    if result.get('quality_summary'):
        print("\n" + "="*80)
        avg_score = result['quality_summary'].get('avg_score', 0)
        count = result['quality_summary'].get('selected_count', 0)
        print(f"Quality Summary: {count} queries selected, avg_score={avg_score}")
        print("="*80)

asyncio.run(test_improved_planner())
