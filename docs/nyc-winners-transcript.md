# NVIDIA Spark Hack NYC — Winners Showcase Transcript

This is the full transcript of the NVIDIA Spark Hack NYC winners showcase, hosted by Barry from the NVIDIA Developer Community team. Same hackathon series as London (Spark Hack → Hack for Impact), same hardware (GB10 Grace Blackwell), same format. Direct precedent for our London entry.

Source: NVIDIA Developer Community livestream / showcase.

---

## Showcase intro

Hey everybody and welcome to the NVIDIA Spark Hack NYC showcase, so glad you're here. I'm Barry, I'm part of the NVIDIA developer community team, and today we get to celebrate some seriously impressive builders.

A few weeks ago, NVIDIA brought the Spark Hack Series to New York City — a hackathon where teams competed to build fully local AI solutions running on NVIDIA's GB10 Grace Blackwell Super Chip. Every team had access to an Acer Veriton GN100 AI mini workstation and they had to build against one of three challenge tracks: human impact, environmental impact, or cultural impact, all using open data from the City of New York. We had 30 teams pushing the limits of on-device AI, and today we're here to spotlight the winners. I'm really excited for you all to see what they've built. Well, let's get into it.

---

## Winner 1 — Project Yara (Ali & Amy)

First off, we've got Project Yara by Ali and Amy. If we can bring them up. All right, you guys want to give a little bit of a background on your project and walk them through what you did?

**Ali:** Hey everyone, this is Ali. Okay, so we built a prototype for small businesses in New York City. Every small business, we think, is an operation which has a bunch of challenges. So currently in the US there are 33 million small businesses which almost have no analyst team — 82% close within five years because they are unable to analyse their data and they have zero budgets for data scientists, because these are typical daily bodegas or salons.

So what we did was basically, we collected the New York City open data source. We indexed around 445 megabytes of data on a local compute, which was a GPU Spark system, and we built a knowledge graph connecting 2,600 nodes. Our system was able to store the DOH restaurant inspections, active licences, the service requests, the permits which are available in a specific zip code where the business is being operational.

So how is it useful for a business? A business just types in the name — so in our use case study, we are showing the famous Katz's, which is a very famous sandwich point in New York City. Our system, just by typing in the name, is able to find everything which this business should be concerned about based on the New York City open data. We enriched all the endpoints which are related to Katz's, and we have a multi-agent harness in the back end which this business can use in order to land on a dashboard like this, where it will be able to see all the permits which it is in violation for, what are the critical DOH violations, what is the throughput or traffic in that specific zip code, who are the competitors for this business, how are they performing on social media platforms, what is their annual / monthly / daily revenue. And they can simply do this by chatting with the interface which you are able to see on the right hand side.

All the information is converted into natural language, and our multi-agentic harness is able to connect with skills and MCP servers in the back end. The major pain point for a small business in New York City is the regulatory risk, or the traffic forecast, or what are the competitors doing. So our system inherently integrates all those endpoints together in order to provide one centralised repository for a small business to query and answer any questions related to that specific business.

Up here you are able to see the regulatory risk for Katz's, then you can see the foot traffic forecast for the coming three days for that specific zip code, so the restaurant can understand what will be the demand and how they can manage their supply. Furthermore, they can see what competitors are selling a similar item, how they're operating. They can see the competitor price, how competitive their pricing is compared to other businesses who are selling the same stuff in the neighbourhood two blocks down the line.

The best and the easiest part for a small business: they can directly chat with the system and they will be able to get the answers customised in their language. The system supports around three languages — Spanish, French and English — but it can be extended based on the LLM provider which we are using in the back end. Furthermore, the system can be integrated with external providers. So this is like a deep dive for a Manhattan suburb where we are able to see how our system is able to build a knowledge graph for all the major pain points or nodes this business encounters with, and our knowledge graph is traversible, so the business doesn't have to open a CSV in order to answer any business-specific question, and the knowledge graph itself can be enriched with more information given a business uploads a CSV or a PDF.

The best part of this entire system is it has MCP servers which can integrate their Stripe account, their Instagram account, their Google Business account, as well as any other social media which they want to monitor in order to see how their business is performing on all the social media, what is their revenue forecast, and what is the sales throughput. Furthermore, we have expanded the system to integrate DoorDash and Uber Eats, so at the end of the day, the business owner can just chat using the chat interface in order to know the daily revenue, daily inventory, and how he or she should be managing the business throughput for the coming few days. If there is a negative review, the multi-agent system automatically replies to Google Business or WhatsApp messages automatically based on the preference of the business. Furthermore, we are also providing several other integrations which is email marketing, menu price comparison, as well as a bunch of other functionality which is in-built using the MCP servers.

The best part of our entire architecture is it's running locally on Spark, so the business doesn't have to worry if they are sharing the information with the external provider or vendor, and they just need to invest on a one-time cost in order to have this device within their shop which will be able to do all those things. All they need is an open-source LLM which they can host locally, and then they can hook it up with all of their external digital providers. And we were able to squeeze out efficiency out of this system, and the entire answer for compliance, revenue and intel will be able to be answered in six seconds using parallel execution.

So inside, there are a bunch of layers — the NYC data layer, the Qwen model, the front end, the Open Claw gateway, and the hardware which is our agentic harness. It's local by design, it's 100% on-device, and it has 1× GB10 desktop which any shop can host locally. So we were the winner for the hackathon, and really excited about getting the RTX 1590. We wanted to expand this to any city and any business, but right now it has been designed on New York City public data in order for it to work for New York's specific businesses located in Manhattan. So this work was done by me and Amy, and this is a publicly available repo, and in future we want to expand it further. So happy to answer any questions if you guys have some.

### Q&A — Project Yara

**Q (Barry):** Are there any other questions in the chat? Okay, Kevin Samson — "ad campaigns for the win, annoys people, it's also how you get eyeballs on what you're selling. What's the advantage of local by design?"

**A (Ali):** So local by design is basically, we want the business not to spend on API credits. Once they acquire a hardware which is a GB10, it's a one-time fixed cost. All they pay for is electricity, and the open agentic harness will automatically be able to update itself as soon as you update the software. So we just want to reduce the overall variable cost for the business, and that is the reason we are building it for local businesses with a local architecture which is GB10.

**Q (Ganopathy Ramkumar):** Can we know the stack and the libraries used in the app?

**A (Ali):** Yeah, so everything is based on open-source stack. We are using Qwen Gemma 4 model as an LLM. We are using Open Claw for the stack, but everything is available on GitHub — it's publicly available, you can see the repo, you can download it, replicate it, you can expand it for your area of your businesses.

**Q:** What's the percent of the whole development was pure AI generated?

**A (Ali):** Great question. So majority of the code was written by AI, but the data scraping, hosting the VLM inference on GB10 — those were customised by us, because the Gemma 4 model endpoint was pretty new when we were building on top of that, and the text-to-speech and speech-to-text was further optimised by me in order for it to be hosted on local consumer hardware. But most of the part was generated — like the front end, the back-end architecture was generated using Claude and OpenAI Codex.

**Q (Utar San):** Would social media influencers assist in the small SMBs?

**A (Ali):** I think the system is agnostic to the MCP server you are hooking it up. So if you want a small business to be attached with a social media influencer, you can connect basically TikTok marketplace for influencers to the existing business, and they can find a mechanism where the SMB is paying the media influencer in order to generate traffic.

**Q (Pronu041):** How many requests per second do you get on average for tokens per second?

**A (Ali):** So the token throughput for Gemma was around 32 tokens per second, but we were using a quantised version, so we were able to get around 60 tokens per second on a local consumer-grade hardware. And I'm talking about text-to-text.

**Q (Sard Muhammad):** If you had one more month to improve the project, what would be your first major feature or optimisation you'd add?

**A (Ali):** The optimisation I would add — we can probably move from Open Claw to Hermes agent because they have much more easier integration available right now. So probably that migration, and making availability for more MCP servers for small businesses. Right now it's just hooked to Stripe, DoorDash and Uber, but would love to expand to other providers too.

**Q (RT Osni):** What are you guys most proud of on this project?

**A (Ali):** We were able to squeeze the entire thing in, I would say, 30 hours.

**Barry:** Wow, that is quite commendable, to do it in 30 hours.

**A (Ali):** I know the project is not perfect, perfect, because it was built in a hackathon in a stretch of 30 hours, but we can improve a lot more.

**Q (Mumini):** What happens when small sellers no longer need to manage operations manually but can instead run their entire business through a conversation with AI?

**A (Ali):** That's the hope. That would be ideal. And I think a sandwich shop which is a historic destination in New York shouldn't be focused on AI — instead, they should focus on what they are good at, and the AI should be able to take care of every external thing which they are doing. Like that is a dream, probably.

**Q (Christian in St Louis):** As on-device agents become more capable and operate in real-time environments, how do you think developers should approach continuous behavioural monitoring — not only model performance, but drift, regime changes, and safety-relevant deviations during execution?

**A (Ali):** This is something — I don't think the edge devices will be able to support the kind of looking inside the model. You would need more high-level — not consumer-grade GPUs but more like a B200 in order to look inside the model and do kind of in-prediction and doing before you deploy it for local use case. But I haven't seen in the market any solution which are doing eval on consumer edge devices as of now.

---

## Winner 2 — Person of Interest (Jay, Pratham, Atul, Raman)

All right, next we have Project Person of Interest by Jay, Pratham, Atul and Raman. You guys want to give a quick overview of your project and kind of run through it?

**Speaker (one of the team):** Yep, awesome. So I hope my screen is visible now. So for the project, Barry did explain the problem statement — it was that we needed to use the NYC open data and then also we needed to run the local models on the NVIDIA hardware that we provided.

So for the hackathon, we decided to build a project called Person of Interest. So it's a real-time predictive risk dashboard for NYC. So what we were trying to do is that we were basically trying to identify all the traffic camera footages that is available to us and check if we are able to analyse if crimes, accidents, incidents are happening in real time and then report them to the organisations or the respective teams that can handle them better.

So what we built was that, firstly, we got all the camera footages live from the NYC traffic website. So these are all live footages that are available right now from the NYC camera footages. So once we were able to hook this up into our website, the second thing we did was we tried to connect a VLM model on the NVIDIA hardware which would keep analysing all these images and do a continuous run of inference, so that it can identify if anything wrong is happening or not.

So we can also ask questions to it, like — so the inference goes on and then we'll get an answer from the AI model as well, that "there is nothing wrong, just a white van and a bus are driving on the street." And whenever there's something incorrect that happens, it flags it and then shows us that, "okay, this thing is happening incorrectly over there," so we can then inform the organisations.

So these are all the camera footages and camera pinpoints that we had available for the project. So this is the entire NYC camera footages uploaded network — so this is all that we have mapped in our system.

The second problem we realised was that running inference on all of these cameras simultaneously is really difficult and like a lot of compute. So what we also made was a dashboard. So this dashboard is basically a good interpretation of where the NYC areas are safe and where not. So we also had access to other open-source datas and open datas which told us about the historical crime rates and the other aspects of that neighbourhood. So we know that this area is generally safer, so we run the inference on this in much lower quantity, in terms of every 3 hours or every 6 hours and not every second. And for areas that we know are highly active in terms of crimes happening or accidents happening, we mark them as red, and then we run inference on these in much higher quantity compared to the safer areas. So this was also part of the dashboard that we built so that we can run continuous inference on the hardware that we provided completely locally.

So this was sort of a project we built to ensure the safety of the NYC city using the public data that we were already having on the internet, and it was not being used appropriately. So we tried to find a use case that could better the data and the NYC as well. So this was the entire project that we built for the hackathon. In the end we won a device — the Spark device as well. So yeah, it was a great being part of the hackathon and thanks NVIDIA, Acer and Antler for organising this. We can go for questions now.

### Q&A — Person of Interest

**Q:** Were you able to automate the issue report?

**A:** Yep, so we were able to identify and categorise the incidents correctly, but we didn't connect it to live sources of like the NYPD or that, because you would need official connections with them to do that. So once we are able to do proper connections with the governments, then we'll be able to send them the reports. But we are able to categorise the request right now.

**Q:** Does it flag speeding van as vehicle of interest, or is it only people it's identifying, or is it also pick up?

**A:** Yeah, so speeding — the problem with this thing is that speeding of vans. The camera footages that are uploaded by NYC is like one frame per second, so the FPS that we get is pretty slow. So we are not able to identify the speed of vehicles because the footage that we get as input from the government is pretty slow and pretty not so accurate. So it's difficult to do that. So it won't do that. It generally classifies people fighting, accidents happened, or more like when people are running over or they're gathering over a group of people. So it's more like incidents and accidents and not like speeding vans and all of that.

**Q (Christopher A):** How do you prevent bias in areas of historically higher crime rates?

**A:** Yep. So in historically higher crime rates — basically, when it comes to bias, it depends upon the model. So currently we using the Llama 3.2 vision model, so it does not really depend upon the area in which we are. If it's a high security or like a high crime rate area, the bias comes from the model. So if a model initially has a bias that it's categorising a community or the segment with higher crime rates in wrong manner, that is something that we need to go ahead with using better models. And it's completely reliant on the model we are using. So we were using the Llama 3.2 vision model, so all of the biasness comes down to the model's training data that Meta had used.

**Q (Manny):** What are the biggest challenges in deploying multimodal AI models for large-scale smart city infrastructure?

**A:** So yeah, basically multimodal is basically very large on compute, and like handling the input data stream and doing inference on such a large data set for a city, it requires a very high terms of compute. And for a city to be able to sponsor it and manage the finances and the expense for that, it's really difficult. And I don't know if taxpayers would be agreeing to do that or not.

**Q (Abishek):** Who can use it, and have you thought of misuses as well, like false alerts — so small crime over here, big crime over here? Is this open to the public for everybody to use?

**A:** So no, did not make it live as of now, so it's not open to public. But the data set is completely open — it's a completely free NYC traffic data set that's live on their website. So regarding abusing this — making this live is difficult because it requires a lot of compute. So if we make it live and a lot of users get onboarded, we are not yet financially capable of hosting all of those users. So we don't have it live right now. And in terms of abusing — it's public data, right? So public data, if we host it or someone else hosted, the probability of it getting abused or used is equally likely. So it does not matter in my opinion.

**Barry:** So you're saying you don't have the funding that Palantir has?

**A:** Yeah, exactly. And we want the funding that Palantir has, but no one is giving it to us.

**Q (Darren 8396):** What model are you using, and what decision factor for its use? Why did you choose that model?

**A:** So we used the 3.2 VLM model, 11 billion parameters. We used it because on the NVIDIA hardware they already had a NIM container for it, which was pretty good in terms of running it and scaling it. And since we had 900 camera footages, we wanted to use a smaller model so we could do multiple inferences together. And we already had the Docker container available for the NIM hardware. So we went with the Llama 3.2 VLM 11 billion model.

**Barry:** NIMs are very, very convenient, I will say that.

**Q (Shelamona):** Is it possible to do this in an air-gapped environment?

**A:** To get the data from the NYC traffic cam, we need to go live, right? So the model is completely local — so we are running the model completely local, we're not connecting to any API or any cloud Google or Gemini subscription. The model is completely running local, but the traffic data that the API sends us comes from the NYC website.

**Q (Anit Kumar Tari):** How would your architecture change for millions of concurrent users from a hackathon?

**A:** Yeah, so onboarding users is not the real challenge. The real challenge comes up when we have much more higher number of camera footages that we need to process. So everyone sees the same output that we are showing, right? So number of users is easier to scale compared to like — for the hackathon we did 950 cameras, and we were not able to do continuous inference, that's why we built the historical dashboard for crimes. Now if you want to do like a live inference for all the cameras concurrently, it requires a lot much higher GPU and like with much higher node compared to a single GPU. So the problem would be coming like onboarding much more camera footages from the government — so that is like very heavy on cost. But onboarding users for them viewing their updates is not that difficult to scale.

**Barry:** Wonderful projects, you guys. This was awesome. Person of Interest is very, very impressive. Congratulations and thank you, Jay, Pratham, Atul and Raman.

---

## Closing — upcoming hackathons

Just so everybody knows, NVIDIA does hackathons all over and you can keep track of them on our Luma calendar. We'll drop a link in the chat. Upcoming ones include:

- **MetaClaw in Taipei** at GTC Taipei and Computex on May 23rd
- **Poolside Research Hackathon in London** on May 29th
- **NVIDIA Spark Hack in Toronto** on May 29th
- **NVIDIA Hack for Impact in London** on June 5th ← *this is us*

So keep posted on that, and thank you to our Spark Hack NYC winners, and thanks for joining everybody. We'll see you on the next one.

---

## Key takeaways (for our London entry)

### What Project Yara did right
- **Multi-agent harness** with MCP servers as the integration surface (Stripe, Instagram, Google Business, DoorDash, Uber Eats, WhatsApp)
- **Knowledge graph** (2,600 nodes) over NYC open data — traversible, queryable in natural language
- **Concrete demo subject** — Katz's Deli, instantly recognisable
- **Quantised model** (Qwen Gemma 4) hitting ~60 tokens/sec on the GB10
- **Multilingual** — 3 languages out of the box
- **Local-by-design** as the value proposition, not just a feature
- **6-second response** with parallel execution
- **30-hour build** — honest about scope
- **Majority of code AI-generated** — Claude + OpenAI Codex

### What Person of Interest did right
- **NIM containers** for fast deployment (Llama 3.2 Vision 11B)
- **Adaptive inference rate** — high-frequency on red zones, low on green (smart compute budgeting)
- **Heat map** as the visual demo hook
- **Pragmatic model choice** — 11B vision model, not the biggest
- **Honest about limits** — 1fps cam feed = no speed detection

### Patterns that map onto London Civic Agent
- MCP servers as the integration story (FixMyStreet, council CRMs, email, WhatsApp, ombudsman)
- Knowledge graph for jurisdictional reasoning (authority → asset type → road segment → SLA)
- Heat map of London issues coloured by severity ranking
- Pick a real, named London location for the demo (the Katz's equivalent)
- Quantise the reasoning model from day one
- Pull NIM containers where possible to save Friday setup time
- Build budget: 30 hours, not 48

### Where we'd beat both NYC winners
- **Outbound voice agent** calling councils via ElevenLabs Conversational AI — neither winner did this, and it's a stronger demo moment than dashboards or heat maps
- **Closed-loop action** — Yara reads/recommends, Person of Interest detects/flags. We file, track, call, escalate. End-to-end action is rarer and harder.
