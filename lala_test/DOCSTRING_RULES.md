# Python Docstring 작성 규칙 (Google Style)

이 문서는 프로젝트 내에서 사용하는 Python Docstring 작성 규칙을 정의합니다. 모든 코드 작성 시 이 규칙을 준수해야 합니다.

## 1. 함수(Function) 생성 규칙

함수 Docstring은 함수의 목적, 인수, 반환값, 예외 등을 명확히 설명해야 합니다.

```python
def function_name(param1, param2):
    """설명:
        함수에 대한 자세한 설명을 여기에 작성
        어떤 일을 하는지, 언제 쓰는지 간단히 풀어서 설명.

    Args:
        param1 (type): 매개변수 1에 대한 설명.
        param2 (type): 매개변수 2에 대한 설명.

    Returns:
        return_type: 반환값에 대한 설명.

    Raises:
        ExceptionType: 어떤 상황에서 예외가 발생하는지.

    생성자:
    생성일자:
    """
    pass
```

## 2. 클래스(Class) 생성 규칙

클래스 Docstring은 클래스의 역할, 속성(Attributes) 등을 설명해야 합니다.

```python
class ClassName:
    """설명:
        클래스의 역할과 책임을 간단히 설명

    Attributes:
        attr1 (type): 속성 설명
        attr2 (type): 속성 설명.

    생성자:
    생성일자:
    """
    def __init__(self):
        pass
```


## 3. Git 커밋 전 주석(Docstring) 확인

주석이 없는 코드가 커밋되는 것을 방지하기 위해 `pre-commit` 훅을 설정하여 검사할 수 있습니다.

### 방법 1: `interrogate` 사용 (문서화 커버리지 체크)

`interrogate`는 코드의 문서화 정도(커버리지)를 체크하여, 일정 수준 이하이면 실패하게 만들 수 있습니다.

1.  **설치**:
    ```bash
    pip install interrogate
    ```

2.  **실행 (수동)**:
    ```bash
    # 문서화가 누락된 항목을 자세히 표시 (-v), private 멤버도 포함 (-p) 등 옵션 사용 가능
    interrogate -v src/
    ```

### 방법 2: `pre-commit` 설정 (자동화)

Git 커밋 시 자동으로 검사하도록 설정합니다.

1.  **`pre-commit` 설치**:
    ```bash
    pip install pre-commit
    ```

2.  **`.pre-commit-config.yaml` 파일 생성**:
    프로젝트 루트에 다음 내용을 작성하여 `interrogate` 또는 `pydocstyle`을 연결합니다.

    ```yaml
    # .pre-commit-config.yaml 예시
    repos:
      - repo: https://github.com/econchick/interrogate
        rev: 1.5.0
        hooks:
          - id: interrogate
            args: [--fail-under=80, -v]  # 문서화 커버리지가 80% 미만이면 커밋 실패
            pass_filenames: false
    ```

3.  **Hook 설치**:
    ```bash
    pre-commit install
    ```

이제 `git commit`을 실행할 때마다 설정한 규칙에 따라 Docstring 존재 여부를 검사하게 됩니다.
