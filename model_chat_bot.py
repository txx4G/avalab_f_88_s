import os
from getpass import getpass
import warnings

warnings.filterwarnings('ignore')

from langchain_openai import ChatOpenAI

os.environ['OPENAI_API_KEY'] = "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"

llm = ChatOpenAI(temperature=0.0)

from langchain.agents import load_tools
from langchain.tools import DuckDuckGoSearchRun
from langchain.chains import LLMMathChain
from langchain.agents import Tool
import langchain
from langchain.agents import AgentType, initialize_agent, load_tools, tool
import os
from getpass import getpass
import warnings
from langchain import hub
import re
from collections import Counter
import time
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

search = DuckDuckGoSearchRun(lang='ru')

# Загрузка инструментов из LangChain
tools = load_tools(["wikipedia"], llm=llm)

# Расширяем инструменты
tools.extend([
    Tool(
        name="Search",
        func=search.run,
        description='Помощник в ответе на вопросы по категориям, ищет информации на русском языке'
    ),
])


def get_user_dialog(prompt_dict_arg, user_question, template_arg):
    '''
    problem
    business_plan
    question
    '''

    template_problem = f'''Твой клиент, который {prompt_dict_arg['stage']} хочет поговорить с тобой о бизнесе в сфере {prompt_dict_arg['sphere']} {prompt_dict_arg['level']} уровня.
    Твоя задача, как эксперта в этой области, ответить на любые вопросы, связанные с бизнесом.

    Если вопрос не относится к бизнесу, отвечай: "Прошу прощения, но не могли бы вы говорить по теме."

    1. **Выявление потребностей клиента**:
    Начни с выявления потребностей клиента. Спроси, какие именно аспекты бизнеса его интересуют, например:
    - Открытие нового бизнеса
    - Поиск финансирования
    - Маркетинг и продвижение
    - Партнёрство и сотрудничество

    На основе ответов клиента составь список его потребностей и уточни, какие элементы бизнеса актуальны в его регионе.

    2. **Разносторонняя информация по интересующей области**:
    Предоставляй разностороннюю информацию по интересующей области. Например:
    - Если клиент хочет открыть бизнес, предложи самые выгодные направления в сфере {prompt_dict_arg['sphere']}, включая идеи по кредитованию и рынкам сбыта.
    - Если интересует финансирование, укажи на самые выгодные банки и условия кредитования.
    - Если клиент интересуется маркетингом или партнёрством, предложи конкретные схемы маркетинга или имена организаций для сотрудничества.

    3. **Предложение бизнес-модели или интересного решения**:
    Предложи бизнес-модель на основе предпочтений клиента, учитывая актуальные тренды и лучшие практики. Это может быть, например, модель франчайзинга, онлайн-магазина или сервиса подписки.

    4. **Список ресурсов для более подробного ознакомления**:
    Для каждого предложения предоставь ссылки на конкретные ресурсы, где клиент может найти дополнительную информацию или решения своих проблем. Обязательно указывай, что ознакомиться подробнее можно на сайте: [ссылка на ресурс].

    Не выдумывай информацию, ответ должен формироваться строго на русском языке, а информация должна браться с конкретных сайтов!

    По окончании диалога с пользователем, предоставь ему ссылки на все использованные ресурсы в виде четкого перечня ссылок.
    '''


    template_bp = f'''ты профессиональных бизнес-аналитик. я {prompt_dict_arg['stage'] },
    хочу запустить {prompt_dict_arg['size'] } бизнес в сфере {prompt_dict_arg['sphere'] }  {prompt_dict_arg['level']  } уровня по модели {prompt_dict_arg['b2']  } уровня в {prompt_dict_arg['region']  } уровня. построй мне бизнес план.
    '''

    template_s = f'''Твой клиент, который {prompt_dict_arg['stage'] } хочет поговорить с тобой о {prompt_dict_arg['size'] } бизнесе в сфере {prompt_dict_arg['sphere'] } {prompt_dict_arg['level']  } уровня . Твоя задача, как эксперта в этой области, ответить на любые вопросы, связанные с бизнесом.
    В случае, если вопрос не относиться к бизнесу, то отвечай: "Прошу прощения, но не могли бы вы говорить по теме."
    Попытайся дать пользователю как можно больше разносторонней информацииобласти, которой он интересуется. Что я имею ввиду, для примера,
    если он желает открыть бизнес - предложи ему самые выгодные направления  в сфере , сферы кредитования, рынки сбыта и так далее. Если его интересует финансирование - предложи самые
    выгодные банки, если же интересует маркетинг или партнёрство - предлагай конкретные схемы маркетинга или конкретных людей/организации для сотрудничества. Также, обязательно
    попытайся предложить пользователю какую-нибудь бизнес модель, основываясь на его предпочтениях. Не выдумывай никакой информации, ответ должен формироваться строго на русском языке, 
    а информация браться с конкретных сайтов! По окончании диалога с пользователем, предоставь ему ссылки на все используемые тобой ресурсы в виде чёткого перечня ссылок.
    \nВопрос пользователя: {user_question}\nОтвет эксперта:
    '''

    template = f'''Вы бизнес-аналитик. Я клиент хочет {prompt_dict_arg['stage'] }. Ваша задача, как эксперта, ответить на его вопросы, основываясь на указанных категориях и проводя поиск по сайтам.
    Если вопрос не подходит под заданную схему, оптимизируйте структуру ответа самостоятельно. Вот его вопрос: {user_question}. Учитывайте местоположение клиента: {prompt_dict_arg['region'] }.
    Краткий и точный ответ: Начните с четкого и понятного ответа на вопрос клиента, сформулированного простым языком
    Обоснование решения: Каждое ваше предложение должно быть конкретизировано. Объясните, почему вы предлагаете именно это решение, и на каких фактах или данных оно основано.
    Приведите примеры из законодательства, если это применимо.
    Подробная информация: Раскройте информацию максимально подробно. Укажите конкретные положения законодательства,
    которые относятся к вопросу клиента, и объясните их с помощью простых примеров. Используйте цитаты из источников,
    чтобы клиент мог видеть, откуда взята информация. Не забудьте объяснить, как эти положения могут повлиять на ситуацию клиента.
    Бизнес-модель: Если это уместно, предложите клиенту бизнес-модель, основанную на его предпочтениях. Укажите банки
    для финансирования и информацию о том, где и как можно реализовать эту бизнес-идею.
    Список источников: В конце ответа укажите ссылки на сайты, с которых вы брали информацию, а также конкретные цитаты,
    которые использовали в ответе.

    Структура ответа:

    1. Выявление потребностей клиента: Определите, что именно хочет клиент.
    2. Разносторонняя информация: Максимально раскройте все предложения и объясните их суть, включая примеры из законодательства.
    3. Предложение по бизнесу: Опишите интересные решения или бизнес-идеи, если это уместно.
    4. Список ресурсов: Укажите конкретные ссылки на страницы, с которых брали информацию.
    5. Краткое резюме: Подведите итог всему вышеописанному, выделив ключевые моменты.

    Важно:
    Только подлинная информация. Ответ должен формироваться строго на русском языке, а информация из
    конкретных сайтов. По вопросам законодательства (НПА) используйте только следующие сайты:

    https://www.garant.ru
    https://www.consultant.ru
    Обязательно объясните некоторые полезные для пользователя положения, взятые из законодательства, описывая
    все подходящие аспекты на доступном языке. Приводите примеры для лучшего понимания.

    Пример завершения ответа:

    "На основе ваших запросов могу предложить... "ваш текст"... Также предлагаю вам реализовать ваш вопрос в этой сфере... "бизнес-идея".
    При генерации ответа была использована информация с следующих источников... Вопрос пользователя: {user_question}'''


    if template_arg == "problem":
        template = template_problem
    elif template_arg == "business_plan":
        template = template_bp
    elif template_arg == "question":
        template = template_s
    
    prompt = PromptTemplate(
        input_variables=["want", "where", "user_question"],
        template=template
    )
        # Инициализация агента
    essay_agent = initialize_agent(
            tools,
            llm,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5
            )
    # Инициализация цепочки LLM. Не забудьте заменить llm на ваш экземпляр LLM!
    chain = LLMChain(llm=llm, prompt=prompt)  # llm должен быть определен ранее

    return essay_agent.run(template)