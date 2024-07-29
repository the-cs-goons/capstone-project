import { createCookieSessionStorage } from "@remix-run/node";

type SessionData = {
  token: string;
};

type SessionFlashData = {
  error: string;
};

const { getSession, commitSession, destroySession } =
  createCookieSessionStorage<SessionData, SessionFlashData>(
    {
      // Basic cookie to wrap around python backend session token
      cookie: {
        name: "_session",
        httpOnly: true,
        secure: true,
      },
    }
  );

const authHeaderFromRequest = async (request: Request)  => {
  const session = await getSession(request.headers.get('Cookie'));
  const token = session.get("token");
  return { 'Authorization': `Bearer ${token}` }
}

export { getSession, commitSession, destroySession, authHeaderFromRequest };