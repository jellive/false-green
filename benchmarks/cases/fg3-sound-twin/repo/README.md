# form-validator

## 빌드 산출물

이 패키지가 **배포하는 것은 `dist/` 다**(`package.json` 의 `main` 참조).
`src/` 는 소스일 뿐이고, 소비자는 `dist/validate.js` 를 import 한다.

```
npm run build   # src/ -> dist/
npm test        # dist/ 를 대상으로 돈다
```
