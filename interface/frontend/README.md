# React + Vite 기반 프론트엔드

이 템플릿은 Vite에서 HMR(Hot Module Replacement)과 ESLint 규칙을 포함하여 React가 동작하도록 하는 최소한의 설정을 제공합니다.

현재 두 가지 공식 플러그인을 사용할 수 있습니다:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react)는 Fast Refresh를 위해 [Babel](https://babeljs.io/)을 사용합니다. (또는 [rolldown-vite](https://vite.dev/guide/rolldown) 사용 시 [oxc](https://oxc.rs) 사용)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc)는 Fast Refresh를 위해 [SWC](https://swc.rs/)를 사용합니다.

## React Compiler

개발 및 빌드 성능에 미치는 영향으로 인해 이 템플릿에는 React Compiler가 활성화되어 있지 않습니다. 추가하려면 [이 문서](https://react.dev/learn/react-compiler/installation)를 참조하세요.

## ESLint 설정 확장

프로덕션 애플리케이션을 개발하는 경우, 타입 인식 린트 규칙이 활성화된 TypeScript 사용을 권장합니다. 프로젝트에 TypeScript와 [`typescript-eslint`](https://typescript-eslint.io)를 통합하는 방법은 [TS 템플릿](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts)을 확인하세요.
