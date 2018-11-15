FROM alpine:3.7

RUN apk add --no-cache nodejs

COPY package.json package-lock.json ./
RUN npm install

ADD ./ /frontend
WORKDIR /frontend
ENV PATH /node_modules/.bin:$PATH

EXPOSE 3000
