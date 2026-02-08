import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

resumes = [
    '백엔드: 단순히 기능을 구현하는 것을 넘어, 대규모 트래픽 환경에서도 안정적으로 동작하는 시스템을 지향합니다. 이전 프로젝트에서 Python과 Django를 기반으로 백엔드 아키텍처를 설계하며...',
    '프론트엔드: 사용자가 마주하는 첫 화면이 서비스의 가치를 결정한다고 믿습니다. React 프레임워크를 활용해 복잡한 UI 구성 요소를 컴포넌트 단위로 설계하고...',
    '인프라: 반복되는 배포 과정을 자동화하여 개발 생산성을 높이는 일에 매력을 느낍니다. AWS EC2 환경에서 서비스를 운영하며 겪었던 수동 배포의 한계...',
    '협업: 성공적인 프로젝트의 핵심은 기술력이 아닌 원활한 소통과 협업 문화에 있다고 생각합니다. 팀 프로젝트 진행 중 발생한 잦은 Git Conflict 문제...',
    '데이터: 데이터 속에 숨겨진 의미를 찾아내어 서비스의 의사결정을 돕는 과정에 보람을 느낍니다. Pandas와 Scikit-learn을 활용하여 대량의 사용자...'
]

questions = [
    'Q1: 대용량 트래픽이 발생할 때 서버의 확장성(Scalability)을 확보하기 위한 전략은?',
    'Q2: REST API 설계 시 리소스 명명 규칙과 HTTP 메서드 활용 원칙을 설명해 주세요.',
    'Q3: React에서 컴포넌트 생명주기에 따른 렌더링 최적화 방법은 무엇인가요?',
    'Q4: 사용자 인터페이스를 설계할 때 가장 우선순위에 두는 가치와 그 이유는?',
    'Q5: CI/CD 파이프라인을 구축할 때 가장 어려웠던 점과 해결 과정을 들려주세요.',
    'Q6: 클라우드 환경에서 보안 그룹(Security Group)과 VPC의 차이점은 무엇인가요?',
    'Q7: 팀 내 기술적 의견 충돌이 발생했을 때 본인만의 설득 노하우가 있나요?',
    'Q8: Git Flow 전략에 대해 설명하고, 브랜치 관리의 중요성을 말해 보세요.',
    'Q9: 모델의 성능 지표 중 정확도(Accuracy) 외에 중요하게 보는 지표가 있나요?',
    'Q10: 대규모 데이터 처리 시 메모리 효율을 높이기 위해 고려해야 할 점은?'
]

ground_truth = [[0,1], [2,3], [4,5], [6,7], [8,9]]

print('��� BGE-M3 벤치마크 시작...')
model = SentenceTransformer('BAAI/bge-m3')
res_vec = model.encode(resumes, normalize_embeddings=True)
que_vec = model.encode(questions, normalize_embeddings=True)
sim_matrix = cosine_similarity(res_vec, que_vec)

final_report = []
categories = ['Backend', 'Frontend', 'Infra', 'Culture', 'Data']

for i in range(len(resumes)):
    top3_idx = np.argsort(sim_matrix[i])[::-1][:3]
    top1_score = sim_matrix[i][top3_idx[0]]
    is_success = any(idx in ground_truth[i] for idx in top3_idx)
    
    final_report.append({
        'Category': categories[i],
        'Top1 Question': questions[top3_idx[0]][:40] + '...',
        'Score': f'{top1_score:.4f}',
        'Success': '✅' if is_success else '❌'
    })

df = pd.DataFrame(final_report)
print('='*60)
print(df.to_string(index=False))
print('='*60)
